"""pingboard worker: checks every target on an interval and stores results.

TODO (weeks 5-6): split into a scheduler that pushes target IDs onto a Redis list
and N workers that BLPOP from it. That gives you something to scale with HPA later.
"""

import logging
import os
import time

import psycopg

from checks import run_all

DATABASE_URL = os.environ["DATABASE_URL"]
INTERVAL = int(os.environ.get("CHECK_INTERVAL_SECONDS", "60"))
TIMEOUT = float(os.environ.get("CHECK_TIMEOUT_SECONDS", "10"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("worker")


def run_once(conn):
    targets = conn.execute("SELECT id, url FROM targets").fetchall()
    for target_id, url in targets:
        r = run_all(url, TIMEOUT)
        conn.execute(
            """INSERT INTO results (target_id, ok, status_code, latency_ms, cert_days_left,
                                      addresses, dns_ms, dns_error, error)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (target_id, r["ok"], r["status_code"], r["latency_ms"], r["cert_days_left"],
             r["addresses"], r["dns_ms"], r["dns_error"], r["error"]),
        )
        log.info("checked %s ok=%s status=%s latency_ms=%s", url, r["ok"], r["status_code"], r["latency_ms"])
    conn.commit()


def main():
    log.info("starting, interval=%ss", INTERVAL)
    while True:
        try:
            with psycopg.connect(DATABASE_URL) as conn:
                run_once(conn)
        except psycopg.Error:
            log.exception("db error, will retry next cycle")
        # TODO: handle SIGTERM so k8s can stop the pod cleanly mid-cycle.
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
