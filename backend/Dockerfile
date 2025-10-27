FROM python:3.11-slim

WORKDIR /app
COPY backend/pyproject.toml ./pyproject.toml
RUN pip install --no-cache-dir poetry \
    && poetry config virtualenvs.create false \
    && poetry install --no-root
COPY backend /app/backend
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
