from collections import defaultdict
from datetime import datetime

SEVERITY_ORDER = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}

_BRUTE_WINDOW     = 60   # seconds
_BRUTE_THRESHOLD  = 5    # failures in window
_SCAN_WINDOW      = 10   # seconds
_SCAN_THRESHOLD   = 10   # 404s in window
_CREDFUZZ_MIN     = 5    # distinct usernames from same IP


def _ts(e) -> float:
    t = e.get("timestamp")
    return t.timestamp() if isinstance(t, datetime) else 0.0


def detect_brute_force(events: list[dict]) -> list[dict]:
    fails: dict[str, list[float]] = defaultdict(list)
    for e in events:
        if e.get("event_type") in ("ssh_fail", "login_fail", "su_fail"):
            ip = e.get("source_ip")
            if ip:
                fails[ip].append(_ts(e))

    incidents = []
    for ip, times in fails.items():
        times.sort()
        for t in times:
            window = [x for x in times if t <= x <= t + _BRUTE_WINDOW]
            if len(window) >= _BRUTE_THRESHOLD:
                incidents.append({
                    "type":      "Brute Force",
                    "severity":  "high",
                    "source_ip": ip,
                    "count":     len(window),
                    "detail":    f"{len(window)} failed logins from {ip} within {_BRUTE_WINDOW}s",
                    "first_seen": datetime.fromtimestamp(window[0]),
                    "last_seen":  datetime.fromtimestamp(window[-1]),
                })
                break
    return incidents


def detect_credential_stuffing(events: list[dict]) -> list[dict]:
    ip_users: dict[str, set] = defaultdict(set)
    ip_times: dict[str, list] = defaultdict(list)
    for e in events:
        if e.get("event_type") in ("ssh_fail", "ssh_invalid", "login_fail"):
            ip   = e.get("source_ip")
            user = e.get("user")
            if ip and user:
                ip_users[ip].add(user)
                ip_times[ip].append(_ts(e))

    incidents = []
    for ip, users in ip_users.items():
        if len(users) >= _CREDFUZZ_MIN:
            times = sorted(ip_times[ip])
            incidents.append({
                "type":      "Credential Stuffing",
                "severity":  "high",
                "source_ip": ip,
                "count":     len(users),
                "detail":    f"{ip} tried {len(users)} usernames: {', '.join(list(users)[:6])}",
                "first_seen": datetime.fromtimestamp(times[0]) if times else None,
                "last_seen":  datetime.fromtimestamp(times[-1]) if times else None,
            })
    return incidents


def detect_privilege_escalation(events: list[dict]) -> list[dict]:
    incidents = []
    for e in events:
        et = e.get("event_type", "")
        ts = e.get("timestamp")
        if et == "sudo_fail":
            incidents.append({
                "type":      "Privilege Escalation Attempt",
                "severity":  "medium",
                "source_ip": None,
                "count":     1,
                "detail":    f"sudo auth failure for user '{e.get('user','?')}'",
                "first_seen": ts,
                "last_seen":  ts,
            })
        elif et == "useradd":
            incidents.append({
                "type":      "New User Created",
                "severity":  "high",
                "source_ip": None,
                "count":     1,
                "detail":    f"New OS account created: '{e.get('user','?')}'",
                "first_seen": ts,
                "last_seen":  ts,
            })
    return incidents


def detect_web_attacks(events: list[dict]) -> list[dict]:
    _type_map = {
        "sqli_attempt":      ("SQL Injection",        "critical"),
        "traversal_attempt": ("Directory Traversal",  "high"),
        "xss_attempt":       ("XSS Attempt",          "high"),
        "scanner_detected":  ("Vulnerability Scanner","medium"),
    }
    ip_buckets: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    for e in events:
        et = e.get("event_type", "")
        if et in _type_map:
            ip_buckets[e.get("source_ip", "unknown")][et].append(e)

    incidents = []
    for ip, types in ip_buckets.items():
        for et, evts in types.items():
            label, sev = _type_map[et]
            ts_list = [_ts(e) for e in evts]
            sample  = evts[0].get("path", evts[0].get("message", ""))[:60]
            incidents.append({
                "type":      label,
                "severity":  sev,
                "source_ip": ip,
                "count":     len(evts),
                "detail":    f"{len(evts)} {label} attempts from {ip} — e.g. {sample}",
                "first_seen": datetime.fromtimestamp(min(ts_list)) if ts_list else None,
                "last_seen":  datetime.fromtimestamp(max(ts_list)) if ts_list else None,
            })
    return incidents


def detect_path_scanning(events: list[dict]) -> list[dict]:
    ip_404: dict[str, list[float]] = defaultdict(list)
    for e in events:
        if e.get("event_type") == "web_404":
            ip = e.get("source_ip")
            if ip:
                ip_404[ip].append(_ts(e))

    incidents = []
    for ip, times in ip_404.items():
        times.sort()
        for t in times:
            window = [x for x in times if t <= x <= t + _SCAN_WINDOW]
            if len(window) >= _SCAN_THRESHOLD:
                incidents.append({
                    "type":      "Directory Brute Force",
                    "severity":  "medium",
                    "source_ip": ip,
                    "count":     len(window),
                    "detail":    f"{len(window)} 404 responses to {ip} in {_SCAN_WINDOW}s",
                    "first_seen": datetime.fromtimestamp(window[0]),
                    "last_seen":  datetime.fromtimestamp(window[-1]),
                })
                break
    return incidents


def detect_custom_log_threats(events: list[dict]) -> list[dict]:
    """Handle structured app/SIEM log events (YYYY-MM-DD LEVEL [service] format)."""
    _DIRECT = {
        "sqli_ids":      ("SQL Injection",              "critical"),
        "port_scan_ids": ("Port Scan",                  "high"),
        "priv_escalate": ("Privilege Escalation",       "high"),
        "brute_fw":      ("Account Lockout / Brute Force", "high"),
        "unauth_api":    ("Unauthorized API Access",    "medium"),
        "high_cpu":      ("High CPU Usage",             "medium"),
        "disk_low":      ("Disk Space Warning",         "low"),
        "app_error":     ("Application Error (5xx)",    "low"),
        "db_timeout":    ("Database Timeout",           "low"),
    }
    incidents = []
    for e in events:
        et = e.get("event_type", "")
        if et in _DIRECT:
            label, sev = _DIRECT[et]
            incidents.append({
                "type":      label,
                "severity":  sev,
                "source_ip": e.get("source_ip"),
                "count":     1,
                "detail":    e.get("message", "")[:140],
                "first_seen": e.get("timestamp"),
                "last_seen":  e.get("timestamp"),
            })
    return incidents


def run_all(events: list[dict]) -> list[dict]:
    all_inc = (
        detect_brute_force(events)
        + detect_credential_stuffing(events)
        + detect_privilege_escalation(events)
        + detect_web_attacks(events)
        + detect_path_scanning(events)
        + detect_custom_log_threats(events)
    )
    all_inc.sort(key=lambda x: SEVERITY_ORDER.get(x["severity"], 0), reverse=True)
    return all_inc
