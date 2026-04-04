FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/pyproject.toml ./pyproject.toml
COPY backend/app/ app/
RUN pip install --no-cache-dir -e '.[firebase,worker]'

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
