"""
detect.py — Threat detection engine for Sentinel.

Each function takes the list of parsed events from parse_logs.py and looks for
a specific attack pattern. They all return a list of incident dicts (or empty).

run_all() is the single entry point the UI calls — it runs every detector and
returns one combined, severity-sorted list.

Why separate functions per threat type?
  Each attack has its own detection logic (rate windows, pattern matching, etc.).
  Keeping them isolated means you can test, tune, or disable one without
  touching the others. It's the same design SOC platforms use for rule sets.
"""

from collections import defaultdict
from datetime import datetime

# Maps severity label → numeric rank for sorting (higher = more severe).
# Used in run_all() to put the worst incidents at the top of the feed.
SEVERITY_ORDER = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}

# ── Detection thresholds ───────────────────────────────────────────────────────
# These mirror real-world SOC alert rules. Tweak them to reduce false positives
# (raise the threshold) or catch stealthier attacks (lower it).
_BRUTE_WINDOW     = 60   # seconds — look at failures within this rolling window
_BRUTE_THRESHOLD  = 5    # failures needed within the window to flag brute force
_SCAN_WINDOW      = 10   # seconds — tight window for directory scanning (fast tool)
_SCAN_THRESHOLD   = 10   # 404s within the window to flag directory brute force
_CREDFUZZ_MIN     = 5    # distinct usernames from the same IP → credential stuffing


def _ts(e) -> float:
    """Return the event's timestamp as a Unix float (seconds since epoch).
    Falls back to 0.0 if the timestamp is missing — safe for comparisons."""
    t = e.get("timestamp")
    return t.timestamp() if isinstance(t, datetime) else 0.0


# ── Brute Force ────────────────────────────────────────────────────────────────

def detect_brute_force(events: list[dict]) -> list[dict]:
    """Detect SSH/login brute-force attacks.

    Algorithm: sliding-window rate detection.
      1. Collect all failed login timestamps, grouped by source IP.
      2. For each IP, sort its failure times and scan forward.
      3. If 5+ failures exist within any 60-second window, flag it.
      4. `break` after the first matching window — one incident per IP,
         not one per window (avoids duplicate alerts).

    Why this threshold?
      5 failures in 60 seconds is the classic fail2ban default rule.
      Legitimate mistyped passwords happen 1-2 times; automated tools fire
      hundreds per second. 5/60s catches automation while ignoring human error.

    Note: this is O(n²) per IP in the worst case. Acceptable for log files
    up to ~100k lines; for production scale, use a deque-based sliding window.
    """
    # Group failure timestamps by source IP
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
            # Count how many failures fall within [t, t + window]
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
                break  # one incident per IP — the first window that triggers
    return incidents


# ── Credential Stuffing ────────────────────────────────────────────────────────

def detect_credential_stuffing(events: list[dict]) -> list[dict]:
    """Detect credential stuffing — using breached username/password pairs.

    The key difference from brute force:
      Brute force = many attempts on ONE account.
      Credential stuffing = ONE attempt on MANY accounts from the same IP.

    An attacker using a breach dump tries each pair exactly once, so the
    per-account failure count stays low enough to evade basic lockout policies.
    The signal is the breadth of usernames from a single IP.
    """
    # Track which usernames each IP attempted, and when
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
                # Show up to 6 usernames so the analyst can cross-check them
                "detail":    f"{ip} tried {len(users)} usernames: {', '.join(list(users)[:6])}",
                "first_seen": datetime.fromtimestamp(times[0])  if times else None,
                "last_seen":  datetime.fromtimestamp(times[-1]) if times else None,
            })
    return incidents


# ── Privilege Escalation ───────────────────────────────────────────────────────

def detect_privilege_escalation(events: list[dict]) -> list[dict]:
    """Detect failed sudo attempts and new OS account creation.

    sudo_fail: a non-root user tried to escalate with sudo and was denied.
      Could be a legitimate mistake, but in an incident context it often
      means a compromised low-priv account probing for escalation paths.

    useradd: a new OS account was created. Adversaries do this to maintain
      persistent access after an initial compromise — MITRE T1136.001.
      ANY useradd in production deserves investigation.

    Both are event-level (one incident per event), not rate-aggregated,
    because even a single occurrence is worth flagging.
    """
    incidents = []
    for e in events:
        et = e.get("event_type", "")
        ts = e.get("timestamp")

        if et == "sudo_fail":
            incidents.append({
                "type":      "Privilege Escalation Attempt",
                "severity":  "medium",
                "source_ip": None,   # sudo failures don't have a remote IP
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


# ── Web Attacks ────────────────────────────────────────────────────────────────

def detect_web_attacks(events: list[dict]) -> list[dict]:
    """Detect SQL injection, directory traversal, XSS, and vulnerability scanners.

    These are detected at parse time (parse_logs.py matches the payload patterns
    in the request path and user-agent). Here we just aggregate them:
    group by source IP + attack type, then emit one incident per unique combo.

    Why aggregate? An attacker firing 200 SQLi attempts should produce ONE
    incident (with count=200), not 200 separate alerts. Aggregation is the
    difference between a usable SIEM and an alert storm.

    Severity is set at parse time via _type_map — SQLi is critical because
    it can exfiltrate the entire database if it lands.
    """
    _type_map = {
        "sqli_attempt":      ("SQL Injection",         "critical"),
        "traversal_attempt": ("Directory Traversal",   "high"),
        "xss_attempt":       ("XSS Attempt",           "high"),
        "scanner_detected":  ("Vulnerability Scanner", "medium"),
    }

    # Bucket events by IP → attack type → list of events
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
            # Grab a sample payload so the analyst knows what was tried
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


# ── Directory Brute Force ──────────────────────────────────────────────────────

def detect_path_scanning(events: list[dict]) -> list[dict]:
    """Detect automated directory/endpoint enumeration via 404 flood.

    Tools like DirBuster and gobuster fire hundreds of GET requests per second
    against wordlists of common paths (/admin, /backup.zip, /.env, etc.).
    The signal is many 404s from the same IP in a very short window (10s).

    Why 10 seconds (not 60 like brute force)?
    Directory scanners are much faster than login brute-forcers because there's
    no authentication round-trip. 10+ 404s in 10s is definitively automated.
    """
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


# ── Structured App Log Threats ─────────────────────────────────────────────────

def detect_custom_log_threats(events: list[dict]) -> list[dict]:
    """Handle events from structured application/SIEM logs.

    These come from the custom log format (YYYY-MM-DD HH:MM:SS LEVEL [service] msg).
    Unlike SSH/web logs, these are pre-categorized by the source system —
    the event_type is already set to a direct label like "sqli_ids" or "port_scan_ids"
    by parse_logs.py. So detection here is just a lookup, not pattern analysis.

    This lets Sentinel ingest logs from any monitoring system that writes
    structured output, not just raw SSH/Apache logs.
    """
    # Maps event_type strings (from parse_logs) → (display label, severity)
    _DIRECT = {
        "sqli_ids":      ("SQL Injection",                "critical"),
        "port_scan_ids": ("Port Scan",                    "high"),
        "priv_escalate": ("Privilege Escalation",         "high"),
        "brute_fw":      ("Account Lockout / Brute Force","high"),
        "unauth_api":    ("Unauthorized API Access",      "medium"),
        "high_cpu":      ("High CPU Usage",               "medium"),
        "disk_low":      ("Disk Space Warning",           "low"),
        "app_error":     ("Application Error (5xx)",      "low"),
        "db_timeout":    ("Database Timeout",             "low"),
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


# ── Main entry point ───────────────────────────────────────────────────────────

def run_all(events: list[dict]) -> list[dict]:
    """Run every detector against the event list and return a unified feed.

    The `+` concatenation combines all incident lists into one. We then sort
    by severity (critical → high → medium → low → info) so the worst threats
    appear first, matching how a real SOC SIEM prioritizes the alert queue.
    """
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
