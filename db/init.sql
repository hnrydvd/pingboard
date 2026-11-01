-- Runs once, on first start of an empty Postgres volume.
-- To re-run: docker compose down -v (this deletes all data).

CREATE TABLE targets (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    url         TEXT NOT NULL UNIQUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE results (
    id              BIGSERIAL PRIMARY KEY,
    target_id       INT NOT NULL REFERENCES targets(id) ON DELETE CASCADE,
    checked_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    ok              BOOLEAN NOT NULL,
    status_code     INT,
    latency_ms      INT,
    cert_days_left  INT,
    error           TEXT
);

CREATE INDEX results_target_checked_idx ON results (target_id, checked_at DESC);

INSERT INTO targets (name, url) VALUES
    ('example', 'https://example.com'),
    ('github',  'https://github.com');
