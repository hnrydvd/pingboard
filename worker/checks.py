"""Check functions. Also runnable on their own for the weeks 1-2 exercise:

    python checks.py https://example.com https://expired.badssl.com
"""

import json
import socket
import ssl
import sys
import time
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx


def check_http(url, timeout=10.0):
    """GET the URL and return status code and latency. Never raises."""
    start = time.monotonic()
    try:
        resp = httpx.get(url, timeout=timeout, follow_redirects=True)
    except httpx.HTTPError as exc:
        return {"ok": False, "status_code": None, "latency_ms": None, "error": str(exc)}
    latency_ms = int((time.monotonic() - start) * 1000)
    return {
        "ok": resp.status_code < 400,
        "status_code": resp.status_code,
        "latency_ms": latency_ms,
        "error": None,
    }


def check_tls(url, timeout=10.0):
    """Return days until the server's TLS certificate expires, or None for plain http.

    TODO (weeks 1-2): implement.
      - Open a socket to (host, port 443) with ssl.create_default_context().wrap_socket(...)
      - getpeercert()["notAfter"] -> parse with ssl.cert_time_to_seconds()
      - Return whole days left. Decide what to do with a cert that fails verification
        (try https://expired.badssl.com).
    """
    if urlparse(url).scheme != "https":
        return None
    return None


def check_dns(url):
    """TODO (weeks 1-2): resolve the hostname with socket.getaddrinfo and
    return the addresses, or an error string. Time it too."""
    return None


def run_all(url, timeout=10.0):
    result = check_http(url, timeout)
    result["cert_days_left"] = check_tls(url, timeout)
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: python checks.py URL [URL ...]")
    for u in sys.argv[1:]:
        print(json.dumps({"url": u, **run_all(u)}))
