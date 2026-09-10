# Dockerfile
# -----------
# Place this file at the ROOT of your libquery folder (next to app/,
# frontend/, .env, requirements.txt) — the same level as this screenshot's
# "libquery" root.

FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copies everything inside app/ (config.py, main.py, database.py,
# ollama_client.py, sql_validator.py, database.sql) into the image.
COPY app/ .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
