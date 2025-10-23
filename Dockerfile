FROM python:3.13-alpine AS builder

# Set environment variables for Python optimization
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apk add --no-cache \
    postgresql-dev \
    gcc \
    musl-dev \
    libpq

WORKDIR /app

COPY pyproject.toml /app/

# Install Python dependencies from pyproject.toml
# Create a minimal setup to satisfy setuptools, then install dependencies
RUN mkdir -p /app/app && \
    echo "# Minimal package for dependency installation" > /app/app/__init__.py && \
    pip install --no-cache-dir /app/ && \
    rm -rf /app/app

# Final stage - create minimal runtime image
FROM python:3.13-alpine

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN apk add --no-cache \
    libpq \
    postgresql-client \
    wget

RUN addgroup -g 1000 appuser && \
    adduser -D -u 1000 -G appuser appuser

WORKDIR /app

# Copy Python dependencies from builder stage
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY --chown=appuser:appuser app/ /app/

RUN mkdir -p /app/staticfiles && \
    chown -R appuser:appuser /app/staticfiles

USER appuser

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
