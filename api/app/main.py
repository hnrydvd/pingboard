"""pingboard API: manages targets and serves check results."""

import os

import psycopg
from fastapi import FastAPI, HTTPException
from prometheus_client import Counter, make_asgi_app
from psycopg.rows import dict_row
from pydantic import BaseModel

DATABASE_URL = os.environ["DATABASE_URL"]

app = FastAPI(title="pingboard")
app.mount("/metrics", make_asgi_app())

targets_created = Counter("pingboard_targets_created_total", "Targets added via the API")


def db():
    # TODO: swap for a connection pool (psycopg_pool) once you load-test this.
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


class TargetIn(BaseModel):
    name: str
    url: str


# --- Health -----------------------------------------------------------------
# Liveness: the process is up. Readiness: it can actually serve (DB reachable).
# These become the k8s livenessProbe / readinessProbe.

@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/readyz")
def readyz():
    try:
        with db() as conn:
            conn.execute("SELECT 1")
    except psycopg.Error as exc:
        raise HTTPException(status_code=503, detail=f"db unavailable: {exc}")
    return {"status": "ready"}


# --- Targets ----------------------------------------------------------------

@app.get("/api/targets")
def list_targets():
    with db() as conn:
        return conn.execute("SELECT * FROM targets ORDER BY id").fetchall()


@app.post("/api/targets", status_code=201)
def create_target(target: TargetIn):
    # TODO: validate the URL scheme (http/https only).
    with db() as conn:
        row = conn.execute(
            "INSERT INTO targets (name, url) VALUES (%s, %s) RETURNING *",
            (target.name, target.url),
        ).fetchone()
    targets_created.inc()
    return row


# TODO: DELETE /api/targets/{id}


# --- Results ----------------------------------------------------------------

@app.get("/api/status")
def status():
    """Latest result per target, for the status page."""
    with db() as conn:
        return conn.execute(
            """
            SELECT DISTINCT ON (t.id)
                   t.id, t.name, t.url, r.checked_at, r.ok,
                   r.status_code, r.latency_ms, r.cert_days_left,
                   r.addresses, r.dns_ms, r.dns_error, r.error
            FROM targets t
            LEFT JOIN results r ON r.target_id = t.id
            ORDER BY t.id, r.checked_at DESC NULLS LAST
            """
        ).fetchall()


# TODO: GET /api/targets/{id}/results?limit=100 for a history view.
