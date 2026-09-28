# syntax=docker/dockerfile:1

# ---------------------------------------------------------
# Stage 1: Build & Static Asset Generation
# ---------------------------------------------------------
FROM node:22-alpine AS builder

WORKDIR /app

# Install dependencies using clean install
COPY package*.json ./
RUN npm ci

# Copy frontend source code and compile production bundle
COPY . .
RUN npm run build

# ---------------------------------------------------------
# Stage 2: Final Minimal Nginx Web Server (<60MB, Zero Node.js)
# ---------------------------------------------------------
FROM nginx:1.27-alpine AS runner

# Install curl for healthcheck validation
RUN apk add --no-cache curl

# Remove default nginx static assets
RUN rm -rf /usr/share/nginx/html/*

# Copy built production assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom nginx configuration (reverse proxy /api, gzip, SPA fallback)
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

# Container Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:80/ || exit 1

# Start Nginx in foreground
CMD ["nginx", "-g", "daemon off;"]
