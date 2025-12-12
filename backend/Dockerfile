# Backend Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install Poetry
RUN pip install poetry==2.2.1

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Install dependencies (production only)
RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-root --no-interaction --no-ansi

# Copy application code and Alembic migrations
COPY app ./app
COPY alembic.ini .
COPY alembic ./alembic

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
