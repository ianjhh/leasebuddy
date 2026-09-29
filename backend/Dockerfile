# backend/Dockerfile

# --- STAGE 1: Build & Install Dependencies (The messy kitchen) ---
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y gcc libpq-dev

# Install Poetry and the export plugin
RUN pip install poetry poetry-plugin-export

# Copy poetry files
COPY pyproject.toml poetry.lock ./

# Export dependencies and install them into their own virtualenv. (With
# `pip install --user`, packages Poetry itself had already installed, such as
# typing-extensions, were skipped and never reached the final image.)
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes
RUN python -m venv /opt/venv && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# --- STAGE 2: Final Image (The clean plate) ---
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y libpq5 curl && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH

COPY . .

EXPOSE 8000

# Hosts such as Render choose the port through $PORT; 8000 otherwise.
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:${PORT:-8000}/health/ || exit 1

CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
