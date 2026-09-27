# backend/Dockerfile

# --- STAGE 1: Build & Install Dependencies (The messy kitchen) ---
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y gcc libpq-dev

# Install Poetry and the export plugin
RUN pip install poetry poetry-plugin-export

# Copy poetry files
COPY pyproject.toml poetry.lock ./

# Export dependencies and install
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes
RUN pip install --user -r requirements.txt

# --- STAGE 2: Final Image (The clean plate) ---
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y libpq5 curl && rm -rf /var/lib/apt/lists/*

COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

COPY . .

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
