# ---- Build stage ----
FROM python:3.13-slim AS builder

WORKDIR /build

COPY pyproject.toml .
RUN pip install --no-cache-dir --prefix=/install .

# ---- Runtime stage ----
FROM python:3.13-slim

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r formforge && useradd -r -g formforge -d /app -s /sbin/nologin formforge

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY alembic.ini .
COPY alembic/ alembic/
COPY src/ src/

# Create data directory for SQLite and set ownership
RUN mkdir -p /app/data && chown -R formforge:formforge /app

# Default environment
ENV FORMFORGE_DATABASE_URL=sqlite+aiosqlite:///./data/formforge.db \
    FORMFORGE_SECRET_KEY=change-me-in-production \
    FORMFORGE_BASE_URL=http://localhost:8000

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Switch to non-root user
USER formforge

# Use exec form for proper signal handling (PID 1)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "src"]
