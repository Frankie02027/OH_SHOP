FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    GARAGE_WORKSPACE_ROOT=/workspace

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY . /app

RUN pip install --no-cache-dir \
    fastapi \
    "uvicorn[standard]" \
    pydantic \
    python-multipart \
    jsonschema \
    referencing

RUN chmod +x /app/compose/ledger/entrypoint.sh

CMD ["sh", "/app/compose/ledger/entrypoint.sh"]
