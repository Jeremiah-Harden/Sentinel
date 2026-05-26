import time
import requests
from functools import lru_cache

_PRIVATE_PREFIXES = (
    "10.", "127.", "::1", "localhost",
    "192.168.", "172.16.", "172.17.", "172.18.", "172.19.",
    "172.20.", "172.21.", "172.22.", "172.23.", "172.24.",
    "172.25.", "172.26.", "172.27.", "172.28.", "172.29.",
    "172.30.", "172.31.",
)

_last_call = [0.0]
_MIN_INTERVAL = 60 / 44  # stay under ip-api.com free limit (45 req/min)


def _is_private(ip: str) -> bool:
    return any(ip.startswith(p) for p in _PRIVATE_PREFIXES)


@lru_cache(maxsize=512)
def geo_lookup(ip: str) -> dict:
    if not ip or _is_private(ip):
        return {"status": "private", "country": "Internal", "city": "", "isp": "", "lat": 0.0, "lon": 0.0}

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
        pass
    return {"status": "error", "country": "Unknown", "city": "", "isp": "", "lat": 0.0, "lon": 0.0}


def enrich_incidents(incidents: list[dict]) -> list[dict]:
    for inc in incidents:
        ip = inc.get("source_ip")
        inc["geo"] = geo_lookup(ip) if ip else {}
    return incidents


def unique_ips(events: list[dict]) -> list[str]:
    return list({e["source_ip"] for e in events if e.get("source_ip")})
