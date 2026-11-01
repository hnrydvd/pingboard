# pingboard

A small uptime and TLS-certificate monitor. A worker checks a list of URLs on a schedule, stores the results in Postgres, and a status page shows what's up, what's down, and which certs are close to expiring.

It's also the app I'm carrying through a year of DevOps practice: Compose → AWS → Kubernetes → Terraform → CI/CD and GitOps → observability.

## Architecture

```
browser ──► frontend (nginx) ──/api──► api (FastAPI) ──► Postgres
                                                           ▲
                         worker (Python) ── checks ────────┘
                              │
                            Redis (queue, coming in weeks 5-6)
```

| Service | Port | Notes |
|---|---|---|
| frontend | 8080 | Static page; nginx proxies `/api/` to the API |
| api | 8000 | `/healthz`, `/readyz`, `/metrics`, `/docs` |
| worker | – | Checks every target every `CHECK_INTERVAL_SECONDS` |
| db | – | Postgres 17; schema in `db/init.sql` |
| redis | – | Not used yet |

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

## Roadmap for this repo (Nov–Dec 2026)

- [ ] **Weeks 1-2:** finish `check_tls` and `check_dns` in `worker/checks.py`; handle timeouts and bad certs cleanly
- [ ] **Weeks 3-4:** multi-stage Dockerfiles; record image sizes before and after below
- [ ] **Weeks 5-6:** scheduler + Redis queue + multiple workers; add-target form; worker metrics
- [ ] **Weeks 7-8:** deploy on EC2 behind an ALB with a Route53 name; nightly `pg_dump` to S3
- [ ] Later: Helm chart (Phase 2), Terraform + CI + Argo CD (Phase 3), Prometheus SLO alerts (Phase 4)

## Image sizes

| Image | Single-stage | Multi-stage |
|---|---|---|
| api | _TBD_ | _TBD_ |
| worker | _TBD_ | _TBD_ |

## What I learned

_Notes, gotchas and decisions go here as I go. These become blog posts later._
