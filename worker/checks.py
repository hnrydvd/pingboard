"""Check functions. Also runnable on their own for the weeks 1-2 exercise:

    python checks.py https://example.com https://expired.badssl.com
"""

import json
import math
import socket
import ssl
import sys
import time
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx
from cryptography import x509


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
    """Return whole days until the server's TLS certificate expires.

    Negative means already expired. None for plain http or if we can't connect.

    Verification is deliberately off here: check_http already reports whether the
    cert is valid, and with verification on, an expired cert raises before we can
    read its expiry date. With it off, getpeercert() returns an empty dict, so we
    take the raw DER bytes and parse them with `cryptography`.
    """
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        return None
    host, port = parsed.hostname, parsed.port or 443

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            # server_hostname sends SNI, so shared hosts return the right cert
            with ctx.wrap_socket(sock, server_hostname=host) as tls:
                der = tls.getpeercert(binary_form=True)
    except (OSError, ssl.SSLError):
        return None
    if not der:
        return None

    not_after = x509.load_der_x509_certificate(der).not_valid_after_utc
    seconds_left = (not_after - datetime.now(timezone.utc)).total_seconds()
    # floor, not int(): a cert that expired 2 hours ago is -1 days, not 0
    return math.floor(seconds_left / 86400)


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
