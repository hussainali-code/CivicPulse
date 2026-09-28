import json
import logging
import sys
import time
import uuid
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from app.config import get_settings
from app.db import check_db_health, engine
from app.providers.cache import check_redis_health, close_redis_client
from app.providers.rate_limiter import RateLimitExceeded
from app.routes import complaints, meta, stats

# Prometheus Metrics Definitions
REQUEST_COUNT = Counter(
    "requests_total",
    "Total count of HTTP requests",
    ["method", "path", "status_code"],
)
REQUEST_LATENCY = Histogram(
    "request_latency_seconds",
    "HTTP request latency in seconds",
    ["method", "path"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)
TRIAGE_LATENCY = Histogram(
    "triage_latency_seconds",
    "AI triage processing latency in seconds",
    ["provider"],
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0],
)
TRIAGE_FALLBACK_COUNT = Counter(
    "triage_fallback_total",
    "Total count of fallback triage invocations",
    ["provider"],
)

settings = get_settings()

# Configure root logger with JSON formatting
class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        if hasattr(record, "extra_info"):
            log_obj.update(record.extra_info)
        return json.dumps(log_obj)

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JsonFormatter())
logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)
logger = logging.getLogger("civicpulse")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup
    logger.info("CivicPulse backend starting up...")
    yield
    # Graceful Shutdown
    logger.info("CivicPulse backend shutting down gracefully...")
    await close_redis_client()
    await engine.dispose()
    logger.info("CivicPulse backend shutdown complete.")


app = FastAPI(
    title="CivicPulse API",
    description="Municipal Complaint Intake and AI Triage Platform",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def json_logging_and_metrics_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    start_time = time.perf_counter()

    # Process request
    response: Response
    try:
        response = await call_next(request)
    except Exception as exc:
        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.error(
            f"Unhandled exception during {request.method} {request.url.path}: {exc!s}",
            extra={"extra_info": {
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "duration_ms": round(duration_ms, 2),
                "status_code": 500,
            }},
            exc_info=True
        )
        REQUEST_COUNT.labels(method=request.method, path=request.url.path, status_code=500).inc()
        raise exc

    duration = time.perf_counter() - start_time
    duration_ms = duration * 1000

    # Add header
    response.headers["X-Request-ID"] = request_id

    # Record Prometheus metrics
    REQUEST_COUNT.labels(
        method=request.method,
        path=request.url.path,
        status_code=response.status_code
    ).inc()
    REQUEST_LATENCY.labels(
        method=request.method,
        path=request.url.path
    ).observe(duration)

    # Structured JSON log (exclude /health from noisy logs if desired, but keep for audit)
    if request.url.path not in ["/health", "/metrics"]:
        logger.info(
            f"{request.method} {request.url.path} -> {response.status_code}",
            extra={"extra_info": {
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
            }}
        )

    return response


@app.get("/health", status_code=status.HTTP_200_OK, tags=["Monitoring"])
async def health() -> dict[str, str]:
    """Liveness probe: returns 200 OK without touching DB or Redis."""
    return {"status": "ok"}


@app.get("/ready", tags=["Monitoring"])
async def ready() -> Response:
    """Readiness probe: checks PostgreSQL and Redis reachability."""
    failed: list[str] = []

    db_ok = await check_db_health()
    if not db_ok:
        failed.append("postgres")

    redis_ok = await check_redis_health()
    if not redis_ok:
        failed.append("redis")

    if failed:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unavailable", "failed": failed},
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "ok"},
    )


@app.get("/metrics", tags=["Monitoring"])
async def metrics() -> Response:
    """Prometheus metrics endpoint."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Transform FastAPI 422 validation errors into 400 Bad Request with field-level details."""
    field_errors = []
    for err in exc.errors():
        loc = err.get("loc", [])
        field_name = str(loc[-1]) if loc else "body"
        field_errors.append({
            "field": field_name,
            "msg": err.get("msg", "Invalid value"),
        })
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": field_errors},
    )


@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(
    request: Request,
    exc: RateLimitExceeded,
) -> JSONResponse:
    """Return 429 Too Many Requests with Retry-After header upon rate limit breach."""
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": exc.detail},
        headers={"Retry-After": str(exc.retry_after)},
    )


# API Routers
app.include_router(complaints.router, prefix="/api", tags=["Complaints"])
app.include_router(meta.router, prefix="/api", tags=["Meta"])
app.include_router(stats.router, prefix="/api", tags=["Stats"])
