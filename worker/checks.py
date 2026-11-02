"""Check functions. Also runnable on their own:

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

# Some sites (e.g. Wikipedia) return 403 to the default "python-httpx/x.y" agent.
# A named agent with a contact URL is what their bot policies ask for.
USER_AGENT = "pingboard/0.1 (+https://github.com/hnrydvd/pingboard)"


def check_http(url, timeout=10.0):
    """GET the URL and return status code and latency. Never raises."""
    start = time.monotonic()
    try:
        resp = httpx.get(
            url, timeout=timeout, follow_redirects=True, headers={"User-Agent": USER_AGENT}
        )
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
    """Resolve the URL's hostname. Returns addresses (IPv4 and IPv6), lookup time,
    and an error string if it didn't resolve. Never raises.

    getaddrinfo has no timeout argument; it uses the system resolver's
    (see /etc/resolv.conf in the container).
    """
    host = urlparse(url).hostname
    if not host:
        return {"addresses": [], "dns_ms": None, "dns_error": "no hostname in URL"}

    start = time.monotonic()
    try:
        # SOCK_STREAM so each address comes back once, not once per socket type
        infos = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        return {"addresses": [], "dns_ms": None, "dns_error": str(exc)}
    dns_ms = int((time.monotonic() - start) * 1000)

    # dict.fromkeys dedupes but keeps resolver order
    addresses = list(dict.fromkeys(info[4][0] for info in infos))
    return {"addresses": addresses, "dns_ms": dns_ms, "dns_error": None}


def run_all(url, timeout=10.0):
    # DNS first: after the HTTP request the OS resolver cache makes dns_ms meaningless
    dns = check_dns(url)
    result = check_http(url, timeout)
    result["cert_days_left"] = check_tls(url, timeout)
    result.update(dns)
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: python checks.py URL [URL ...]")
    for u in sys.argv[1:]:
        print(json.dumps({"url": u, **run_all(u)}))
