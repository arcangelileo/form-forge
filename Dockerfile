FROM python:3.13-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copy application code
COPY alembic.ini .
COPY alembic/ alembic/
COPY src/ src/

# Create data directory for SQLite
RUN mkdir -p /app/data

ENV FORMFORGE_DATABASE_URL=sqlite+aiosqlite:///./data/formforge.db
ENV FORMFORGE_SECRET_KEY=change-me-in-production
ENV FORMFORGE_BASE_URL=http://localhost:8000

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "src"]
