# pingboard

A small uptime and TLS-certificate monitor. A worker checks a list of URLs on a schedule, stores the results in Postgres, and a status page shows what's up, what's down, and which certs are close to expiring.

## Architecture

```
browser ──► frontend (nginx) ──/api──► api (FastAPI) ──► Postgres
                                                           ▲
                         worker (Python) ── checks ────────┘
```

| Service | Port | Notes |
|---|---|---|
| frontend | 8080 | Static page; nginx proxies `/api/` to the API |
| api | 8000 | `/healthz`, `/readyz`, `/metrics`, `/docs` |
| worker | – | Checks every target every `CHECK_INTERVAL_SECONDS` |
| db | – | Postgres 17; schema in `db/init.sql` |

## Run locally

```bash
cp .env.example .env
docker compose up --build
```

- Status page: http://localhost:8080
- API docs: http://localhost:8000/docs
- Add a target: `curl -X POST localhost:8000/api/targets -H 'content-type: application/json' -d '{"name":"mysite","url":"https://example.org"}'`
- Reset the DB: `docker compose down -v`

Run the checks without containers:

```bash
cd worker && python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python checks.py https://example.com https://expired.badssl.com
```
