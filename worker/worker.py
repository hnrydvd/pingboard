"""pingboard worker: checks every target on an interval and stores results."""

import logging
import os
import signal
import threading

import psycopg

from checks import run_all

DATABASE_URL = os.environ["DATABASE_URL"]
INTERVAL = int(os.environ.get("CHECK_INTERVAL_SECONDS", "60"))
TIMEOUT = float(os.environ.get("CHECK_TIMEOUT_SECONDS", "10"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("worker")

# Set by SIGTERM. As PID 1 with no handler, Python would ignore the signal and
# wait to be SIGKILLed at the end of the grace period.
stop = threading.Event()


def check(url):
    """run_all, but one bad target can't stop the checks for the others."""
    try:
        return run_all(url, TIMEOUT)
    except Exception as exc:
        log.exception("check failed for %s", url)
        return {"ok": False, "status_code": None, "latency_ms": None, "cert_days_left": None,
                "addresses": [], "dns_ms": None, "dns_error": None, "error": str(exc)}


def run_once(conn):
    targets = conn.execute("SELECT id, url FROM targets").fetchall()
    for target_id, url in targets:
        if stop.is_set():
            break
        r = check(url)
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
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    log.info("starting, interval=%ss", INTERVAL)
    while not stop.is_set():
        try:
            with psycopg.connect(DATABASE_URL) as conn:
                run_once(conn)
        except psycopg.Error:
            log.exception("db error, will retry next cycle")
        stop.wait(INTERVAL)
    log.info("stopped")


if __name__ == "__main__":
    main()
