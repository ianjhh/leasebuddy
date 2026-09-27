#!/usr/bin/env bash
# Waits for Docker, brings up Postgres + Redis, then runs every eval that needs
# live infrastructure and writes the results under backend/results/.
#
# Safe to launch before Docker is running: it polls for the engine first.
set -u

PY=./venv/Scripts/python.exe
COMPOSE=../infra/docker/docker-compose.yml
LOG_PREFIX="[run_all]"

log() { echo "$LOG_PREFIX $*"; }

# ---- 1. wait for the docker engine ----------------------------------------
log "waiting for the docker engine (up to 30 min)..."
for _ in $(seq 1 360); do
  if docker info >/dev/null 2>&1; then
    log "docker engine is up"
    break
  fi
  sleep 5
done

if ! docker info >/dev/null 2>&1; then
  log "ERROR: docker engine never came up; aborting"
  exit 1
fi

# ---- 2. start only postgres + redis ----------------------------------------
# The compose file also defines an ollama service; we deliberately skip it so it
# does not fight the native Ollama already serving :11434.
log "starting postgres and redis..."
docker compose -f "$COMPOSE" up -d postgres redis || {
  log "ERROR: compose up failed"; exit 1;
}

log "waiting for postgres to accept connections..."
for _ in $(seq 1 60); do
  if docker compose -f "$COMPOSE" exec -T postgres pg_isready -U postgres >/dev/null 2>&1; then
    log "postgres is ready"
    break
  fi
  sleep 2
done

# ---- 3. ingest the corpus through the production indexer -------------------
log "ingesting corpus..."
$PY -u -m evals.ingest_corpus 2>&1 | tail -20 || { log "ERROR: ingest failed"; exit 1; }

# ---- 4. retrieval ablation -------------------------------------------------
log "running retrieval eval (hybrid vs vector vs keyword)..."
$PY -u -m evals.run_retrieval_eval --out results/retrieval.json 2>&1 | tail -40

# ---- 5. end-to-end generation through real retrieval ----------------------
log "running end-to-end generation eval..."
$PY -u -m evals.run_generation_eval --mode e2e --concurrency 3 \
    --model llama3.1:8b --out results/gen_e2e.json 2>&1 | tail -40

# ---- 6. bring up the API and verify the infra claims ----------------------
log "starting the API for infrastructure checks..."
$PY -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --log-level warning \
    > ../api_server.log 2>&1 &
API_PID=$!
sleep 15

log "running infrastructure eval..."
$PY -u -m evals.run_infra_eval --api http://127.0.0.1:8000 --out results/infra.json 2>&1 | tail -60

log "stopping the API (pid $API_PID)"
kill "$API_PID" 2>/dev/null || true

log "DONE. Results in backend/results/"
