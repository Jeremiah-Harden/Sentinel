"""
ip_intel.py — IP geolocation enrichment for Sentinel.

Uses ip-api.com's free JSON API (no key required, 45 req/min limit).
Results are cached in memory so the same IP is never looked up twice
during a single analysis run.

Why enrich incidents with geo data?
  Raw IP addresses have no meaning to a human reader. Adding country, city,
  ISP, and coordinates turns "185.220.101.1 failed 47 times" into
  "Tor exit node, Nuremberg, Germany — known attacker infrastructure".
  It also powers the attack origin world map in the dashboard.
"""

import time
import requests
from functools import lru_cache

# ── Private IP ranges ──────────────────────────────────────────────────────────
# These IPs are internal network addresses (RFC 1918) or loopback.
# ip-api.com can't geolocate them and would return an error, so we short-circuit.
# The 172.16-31.x ranges cover Docker, VPNs, and corporate networks.
_PRIVATE_PREFIXES = (
    "10.", "127.", "::1", "localhost",
    "192.168.",
    "172.16.", "172.17.", "172.18.", "172.19.",
    "172.20.", "172.21.", "172.22.", "172.23.", "172.24.",
    "172.25.", "172.26.", "172.27.", "172.28.", "172.29.",
    "172.30.", "172.31.",
)

# ── Rate limiting ──────────────────────────────────────────────────────────────
# ip-api.com free tier: 45 requests/minute → one request every ~1.33 seconds.
# We store the last call time in a mutable list (not a plain float) because
# Python closures can't rebind outer-scope primitives — only mutate containers.
# (In Python 3.x you'd use `nonlocal`, but lru_cache functions can't do that
#  cleanly. The one-element list trick is idiomatic for this pattern.)
_last_call    = [0.0]
_MIN_INTERVAL = 60 / 44  # stay comfortably under the 45 req/min limit


def _is_private(ip: str) -> bool:
    """Return True if the IP is a private/loopback address that can't be geolocated."""
    return any(ip.startswith(p) for p in _PRIVATE_PREFIXES)


@lru_cache(maxsize=512)
def geo_lookup(ip: str) -> dict:
    """Resolve a public IP to geographic and ISP metadata.

    @lru_cache stores results in memory keyed by IP string. If the same IP
    appears in 50 incidents, the API is only called once — the other 49 hits
    return the cached dict instantly. maxsize=512 keeps ~512 unique IPs in cache
    (plenty for a single log analysis run).

    Returns a dict with: status, country, countryCode, regionName, city,
                         isp, org, lat, lon.
    On failure, returns a safe fallback dict so callers don't need to check.
    """
    if not ip or _is_private(ip):
        return {"status": "private", "country": "Internal", "city": "", "isp": "", "lat": 0.0, "lon": 0.0}

    # Enforce rate limit: sleep only as long as needed to hit the interval
    elapsed = time.time() - _last_call[0]
    if elapsed < _MIN_INTERVAL:
        time.sleep(_MIN_INTERVAL - elapsed)
    _last_call[0] = time.time()

    try:
        r = requests.get(
            f"http://ip-api.com/json/{ip}",
            params={"fields": "status,country,countryCode,regionName,city,isp,org,lat,lon"},
            timeout=5,
        )
        data = r.json()
        if data.get("status") == "success":
            return data
    except Exception:
        pass   # network error, timeout, or bad JSON — return fallback below

    return {"status": "error", "country": "Unknown", "city": "", "isp": "", "lat": 0.0, "lon": 0.0}


def enrich_incidents(incidents: list[dict]) -> list[dict]:
    """Add a 'geo' key to every incident that has a source_ip.

    Modifies the list in-place AND returns it so callers can chain:
        incidents = enrich_incidents(incidents)

    Incidents without a source_ip (e.g., local sudo failures) get an empty geo dict.
    """
    for inc in incidents:
        ip = inc.get("source_ip")
        inc["geo"] = geo_lookup(ip) if ip else {}
    return incidents


def unique_ips(events: list[dict]) -> list[str]:
    """Return a deduplicated list of source IPs from a list of events.
    Used by the dashboard to count distinct attacker IPs for the KPI row."""
    return list({e["source_ip"] for e in events if e.get("source_ip")})
