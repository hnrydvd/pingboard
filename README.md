# pingboard

A small uptime and TLS-certificate monitor. A worker checks a list of URLs on a schedule, stores the results in Postgres, and a status page shows what's up, what's down, and which certs are close to expiring.

It's also the app I'm carrying through a year of DevOps practice: Compose → AWS → Terraform basics → Kubernetes → CI/CD and GitOps → observability.

## Architecture

```
browser ──► frontend (nginx) ──/api──► api (FastAPI) ──► Postgres
                                                           ▲
                         worker (Python) ── checks ────────┘
                              │
                            Redis (queue, coming in Phase 2)
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

## Roadmap for this repo (Nov 2026–Oct 2027)

No new work is planned here for Nov–Dec 2026, while Linux and the RHCSA come first.

- [x] **Done:** finish `check_tls` and `check_dns` in `worker/checks.py`; handle timeouts and bad certs cleanly
- [ ] **Phase 2 (Jan–Mar 2027):** multi-stage Dockerfiles; record image sizes before and after below
- [ ] **Phase 2:** scheduler + Redis queue + multiple workers; add-target form; worker metrics
- [ ] **Phase 2:** deploy on EC2 by hand behind an ALB with a Route53 name; nightly `pg_dump` to S3
- [ ] **Phase 2 (Feb–Mar):** rebuild the EC2 deployment in Terraform
- [ ] **Phase 3 (Apr–Jun):** Helm chart
- [ ] **Phase 4 (Jul–Aug):** Terraform for VPC + EKS; CI; Argo CD
- [ ] **Phase 5 (Sep–Oct):** Prometheus SLO alerts

## Image sizes

| Image | Single-stage | Multi-stage |
|---|---|---|
| api | _TBD_ | _TBD_ |
| worker | _TBD_ | _TBD_ |

## What I learned

_Notes, gotchas and decisions go here as I go. These become blog posts later._
