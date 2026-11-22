# ==========================================
# STAGE 0: Frontend Build (Debian GLIBC)
# ==========================================
FROM node:20-slim AS web-builder

WORKDIR /app

# Copy root workspace and package manifests
COPY package*.json ./
COPY packages/shared ./packages/shared/
COPY apps/web ./apps/web/

# Install dependencies using workspaces and build frontend
RUN npm install
RUN npm --prefix apps/web run build

# ==========================================
# STAGE 1: Python Builder
# ==========================================
FROM python:3.12-slim AS builder

WORKDIR /build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY packages/ml /build/packages/ml
COPY apps/api /build/apps/api

RUN pip install --upgrade pip && \
    pip wheel --no-cache-dir --wheel-dir=/build/wheels \
    -r /build/packages/ml/requirements.txt \
    -r /build/apps/api/requirements.txt

# ==========================================
# STAGE 2: Production Runtime
# ==========================================
FROM python:3.12-slim AS runner

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app:/app/packages/ml \
    ENVIRONMENT=production

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /build/wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels /wheels/* && rm -rf /wheels

# Copy application source
COPY packages /app/packages
COPY apps/api /app/apps/api
COPY --from=web-builder /app/apps/web/dist /app/apps/web/dist

# Install ML package into Python environment
RUN pip install --no-cache-dir -e /app/packages/ml

# Create non-root user and ensure permissions
RUN useradd -m -u 1000 oracle && chown -R oracle:oracle /app
USER oracle

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/healthz || exit 1

CMD ["sh", "-c", "python -m uvicorn apps.api.src.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
