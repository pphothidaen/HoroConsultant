# ============================================================
# Dockerfile — Computational Metaphysics Engine
# Base: Ubuntu 22.04 LTS
# Services: FastAPI + Ollama (via sidecar in docker-compose)
# ============================================================

FROM ubuntu:22.04 AS base

LABEL maintainer="Computational Metaphysics Engine"
LABEL version="1.0.0"
LABEL description="BaZi Computation Engine + Ollama Inference Service"

# System dependencies
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3-pip \
    curl \
    wget \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set python3.11 as default
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 \
    && update-alternatives --install /usr/bin/python  python  /usr/bin/python3.11 1

# ============================================================
# Python dependencies stage
# ============================================================
FROM base AS python-deps

WORKDIR /install

COPY requirements.txt .
RUN pip3 install --no-cache-dir --upgrade pip \
    && pip3 install --no-cache-dir -r requirements.txt

# ============================================================
# Application stage
# ============================================================
FROM python-deps AS app

WORKDIR /app

# Copy source
COPY project/  ./project/
COPY tests/    ./tests/
COPY scripts/  ./scripts/

# Copy config files
COPY .env.example .env.example

# Non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser \
    && chown -R appuser:appuser /app
USER appuser

# Expose FastAPI port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command: run FastAPI server
CMD ["python3", "-m", "uvicorn", "project.main:app", \
     "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
