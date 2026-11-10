"""pingboard API: manages targets and serves check results."""

import os
from urllib.parse import urlsplit

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

def is_checkable(url):
    """True for an http(s) URL with a hostname and a valid port."""
    try:
        parts = urlsplit(url)
        parts.port  # raises ValueError if out of range
    except ValueError:
        return False
    return parts.scheme in ("http", "https") and bool(parts.hostname)


@app.get("/api/targets")
def list_targets():
    with db() as conn:
        return conn.execute("SELECT * FROM targets ORDER BY id").fetchall()


@app.post("/api/targets", status_code=201)
def create_target(target: TargetIn):
    if not is_checkable(target.url):
        raise HTTPException(status_code=422, detail="url must be http or https with a hostname")
    try:
        with db() as conn:
            row = conn.execute(
                "INSERT INTO targets (name, url) VALUES (%s, %s) RETURNING *",
                (target.name, target.url),
            ).fetchone()
    except psycopg.errors.UniqueViolation:
        raise HTTPException(status_code=409, detail="url already exists")
    targets_created.inc()
    return row


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
