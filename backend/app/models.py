import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Index,
    Integer,
    String,
    desc,
    func,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Category(str, enum.Enum):
    WATER = "water"
    ELECTRICITY = "electricity"
    SANITATION = "sanitation"
    ROADS = "roads"
    STREETLIGHTS = "streetlights"
    OTHER = "other"


class Priority(str, enum.Enum):
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class Status(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    REJECTED = "rejected"


class Complaint(Base):
    __tablename__ = "complaints"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    text: Mapped[str] = mapped_column(
        String(2000),
        nullable=False
    )
    location: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )
    reporter_contact: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )
    category: Mapped[Category] = mapped_column(
        SQLEnum(Category, name="category_enum", values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    priority: Mapped[Priority] = mapped_column(
        SQLEnum(Priority, name="priority_enum", values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    status: Mapped[Status] = mapped_column(
        SQLEnum(Status, name="status_enum", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=Status.OPEN
    )
    ai_summary: Mapped[str | None] = mapped_column(
        String(140),
        nullable=True
    )
    triaged_by: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )
    triage_latency_ms: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint("char_length(text) >= 10", name="chk_text_min_length"),
        CheckConstraint("char_length(location) >= 3", name="chk_location_min_length"),
        Index("idx_complaints_status_priority", "status", "priority"),
        Index("idx_complaints_created_at", desc("created_at")),
    )
