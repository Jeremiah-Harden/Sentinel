"""
parse_logs.py — Log parser for Sentinel.

Converts raw log text into a list of structured event dicts that detect.py
can analyze. Supports three formats automatically:

  1. syslog  — Linux auth.log / syslog ("Jan  3 04:22:01 server sshd[1234]: ...")
  2. apache  — Apache/Nginx access log (Combined Log Format)
  3. custom  — Structured app/SIEM log ("YYYY-MM-DD HH:MM:SS LEVEL [service] msg")

Why regex-based parsing instead of a library?
  Log formats vary between distros, nginx versions, and apps. Hand-written
  regexes give precise control and are easy to extend for new formats.
  Libraries like `loguru` parse their own format, not arbitrary system logs.
"""

import re
import gzip
from datetime import datetime
from pathlib import Path

# Month abbreviation → month number (used by syslog timestamps like "Jan  3")
_MONTH = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
}

# ── Syslog regex ───────────────────────────────────────────────────────────────
# Matches: "Jan  3 04:22:01 hostname sshd[1234]: message text"
#          "May 15 12:00:00 myserver sudo: ..."
# Named groups make the extraction code below self-documenting.
_SYSLOG_RE = re.compile(
    r"^(?P<month>\w{3})\s{1,2}(?P<day>\d+)\s(?P<time>\d{2}:\d{2}:\d{2})\s"
    r"(?P<host>\S+)\s(?P<proc>[^\[:]+)(?:\[(?P<pid>\d+)\])?:\s*(?P<msg>.+)$"
)

# ── Apache Combined Log Format regex ──────────────────────────────────────────
# Matches: 192.168.1.1 - - [03/Jan/2024:04:22:01 +0000] "GET /path HTTP/1.1" 200 1234
# The referer and user-agent at the end are optional (some configs omit them).
_APACHE_RE = re.compile(
    r"^(?P<ip>\S+)\s+\S+\s+\S+\s+\[(?P<time>[^\]]+)\]\s+"
    r'"(?P<method>[A-Z]+)\s+(?P<path>\S+)\s+\S+"\s+(?P<status>\d+)\s+(?P<size>\S+)'
    r'(?:\s+"(?P<referer>[^"]*)"\s+"(?P<ua>[^"]*)")?'
)

# ── Auth log patterns ──────────────────────────────────────────────────────────
# These extract structured fields from the message portion of a syslog line.
# Each key becomes the event_type; capture groups supply user/IP data.
_AUTH_PATTERNS = {
    "ssh_fail":      re.compile(r"Failed (?:password|publickey) for (?:invalid user )?(\S+) from (\S+) port \d+"),
    "ssh_accept":    re.compile(r"Accepted (?:password|publickey) for (\S+) from (\S+) port \d+"),
    "ssh_invalid":   re.compile(r"Invalid user (\S+) from (\S+)"),
    "sudo_fail":     re.compile(r"authentication failure.*?user=(\S+)"),
    "sudo_cmd":      re.compile(r"(\S+)\s*:\s*TTY=\S+\s*;\s*PWD=\S+\s*;\s*USER=(\S+)\s*;\s*COMMAND=(.+)"),
    "useradd":       re.compile(r"new user: name=([^,]+)"),
    "passwd_change": re.compile(r"password changed for (\S+)"),
    "su_fail":       re.compile(r"FAILED su for (\S+) by (\S+)"),
}

# ── Web attack signatures ──────────────────────────────────────────────────────
# Applied to the request PATH in Apache log lines.
# SQLi: looks for common injection keywords — UNION SELECT, DROP TABLE, etc.
_SQLI_RE = re.compile(
    r"(?i)(union\s+select|select\s+.+\s+from|insert\s+into|drop\s+table|"
    r"exec\s*\(|xp_cmdshell|'--|%27--|or\s+1=1|and\s+1=1|"
    r"information_schema|sysobjects|syscolumns)"
)
# Traversal: ../ and URL-encoded variants (%2e%2e%2f, %252e double-encoded)
_TRAVERSAL_RE = re.compile(r"\.\.\/|\.\.\\|%2e%2e%2f|%252e", re.I)
# XSS: script injection and event handler injection patterns
_XSS_RE = re.compile(r"(?i)(<script|javascript:|onerror=|onload=|alert\s*\()")
# Scanner UA: well-known vulnerability scanner user-agent strings
_SCANNER_UA_RE = re.compile(
    r"(?i)(sqlmap|nikto|nmap|masscan|dirbuster|gobuster|wfuzz|burpsuite|"
    r"acunetix|nessus|openvas|w3af|skipfish|havij|zgrab)"
)

# ── Custom / structured app log format ────────────────────────────────────────
# Format: "YYYY-MM-DD HH:MM:SS LEVEL [service] message"
# This lets Sentinel ingest logs from any app that writes structured output.
_CUSTOM_LOG_RE = re.compile(
    r"^(?P<date>\d{4}-\d{2}-\d{2})\s+(?P<time>\d{2}:\d{2}:\d{2})\s+"
    r"(?P<level>INFO|WARN|ERROR|ALERT|DEBUG|CRITICAL)\s+\[(?P<service>[^\]]+)\]\s+(?P<msg>.+)$"
)
# General IP extractor — used to pull source IPs from free-text log messages
_IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")

# Maps message patterns in custom logs → structured event types
# These parallel the event types that detect.py knows how to handle
_CUSTOM_PATTERNS = {
    "sqli_ids":      re.compile(r"SQL injection attempt detected.*from (\S+)"),
    "port_scan_ids": re.compile(r"[Pp]ort scan detected from (\S+)"),
    "brute_fw":      re.compile(r"[Bb]locked IP (\S+).*exceeded \d+ login"),
    "login_fail":    re.compile(r"[Ff]ailed login for user '?(\S+?)'? from (\S+)"),
    "priv_escalate": re.compile(r"elevated privileges"),
    "unauth_api":    re.compile(r"[Uu]nauthorized API access"),
    "high_cpu":      re.compile(r"[Hh]igh CPU.*\((\d+)%\)"),
    "disk_low":      re.compile(r"[Dd]isk space low.*?(\d+)%"),
    "app_error":     re.compile(r"5\d{2} (?:Internal Server Error|Bad Gateway|Service Unavailable)"),
    "db_timeout":    re.compile(r"[Cc]onnection timeout to database"),
}


# ── Timestamp parsers ──────────────────────────────────────────────────────────

def _syslog_ts(m) -> datetime:
    """Build a datetime from syslog's 'Jan  3 04:22:01' format.
    Syslog omits the year, so we assume the current year. This breaks
    across January 1st for old logs but is acceptable for recent data."""
    year = datetime.now().year
    mon  = _MONTH.get(m.group("month"), 1)
    day  = int(m.group("day"))
    h, mi, s = (int(x) for x in m.group("time").split(":"))
    return datetime(year, mon, day, h, mi, s)


def _apache_ts(s: str) -> datetime:
    """Parse Apache's timestamp format: '03/Jan/2024:04:22:01 +0000'.
    Only the first 20 characters are needed (the timezone offset is discarded)."""
    try:
        return datetime.strptime(s[:20], "%d/%b/%Y:%H:%M:%S")
    except ValueError:
        return datetime.now()


# ── Line parsers ───────────────────────────────────────────────────────────────

def _parse_syslog_line(line: str) -> dict | None:
    """Parse one syslog line into a structured event dict.

    Returns None if the line doesn't match syslog format (caller skips it).
    Starts with a generic 'syslog' event_type, then tries each auth pattern
    to narrow it down to a specific event like 'ssh_fail' or 'useradd'.
    The first matching pattern wins (break after match).
    """
    m = _SYSLOG_RE.match(line)
    if not m:
        return None

    msg  = m.group("msg")
    proc = m.group("proc").strip()
    ts   = _syslog_ts(m)

    # Base event — all syslog lines get these fields at minimum
    base = {
        "timestamp":  ts,
        "source_ip":  None,
        "user":       None,
        "event_type": "syslog",   # overwritten below if a pattern matches
        "message":    msg,
        "raw":        line,
        "process":    proc,
    }

    # Try each auth pattern against the message portion
    for evt, pat in _AUTH_PATTERNS.items():
        hit = pat.search(msg)
        if not hit:
            continue
        g = hit.groups()
        if evt in ("ssh_fail", "ssh_accept", "ssh_invalid"):
            base["user"]       = g[0]
            base["source_ip"]  = g[1]
            base["event_type"] = evt
        elif evt == "sudo_fail":
            base["user"]       = g[0]
            base["event_type"] = evt
        elif evt == "sudo_cmd":
            base["user"]       = g[0]
            base["event_type"] = evt
            base["message"]    = f"sudo: {g[0]} ran as {g[1]}: {g[2]}"
        elif evt in ("useradd", "passwd_change"):
            base["user"]       = g[0]
            base["event_type"] = evt
        elif evt == "su_fail":
            base["user"]       = g[0]
            base["event_type"] = evt
        break   # only the first matching pattern applies
    return base


def _parse_apache_line(line: str) -> dict | None:
    """Parse one Apache/Nginx Combined Log Format line.

    After extracting the basic fields (IP, path, status, UA), applies attack
    signatures in priority order:
      SQLi > traversal > XSS > scanner UA > 404 > 5xx > normal request
    Only the first matching attack type is recorded — a request can't be both
    SQLi and XSS (the attacker chose one payload).
    """
    m = _APACHE_RE.match(line)
    if not m:
        return None

    ip     = m.group("ip")
    ts     = _apache_ts(m.group("time"))
    method = m.group("method")
    path   = m.group("path")
    status = int(m.group("status"))
    ua     = m.group("ua") or ""

    # Determine event type by inspecting path and user-agent for attack patterns
    evt = "web_request"   # default — no attack detected
    if _SQLI_RE.search(path):
        evt = "sqli_attempt"
    elif _TRAVERSAL_RE.search(path):
        evt = "traversal_attempt"
    elif _XSS_RE.search(path):
        evt = "xss_attempt"
    elif _SCANNER_UA_RE.search(ua):
        evt = "scanner_detected"
    elif status == 404 and method == "GET":
        evt = "web_404"    # used by detect_path_scanning to find dir brute-force
    elif status >= 500:
        evt = "web_error"

    return {
        "timestamp":   ts,
        "source_ip":   ip,
        "user":        None,
        "event_type":  evt,
        "status_code": status,
        "method":      method,
        "path":        path,
        "user_agent":  ua,
        "message":     f"{method} {path} → {status}",
        "raw":         line,
        "process":     "httpd",
    }


def _parse_custom_line(line: str) -> dict | None:
    """Parse one structured application/SIEM log line.

    Extracts the timestamp, level, service, and message from the custom format,
    then tries each custom pattern against the message to assign a specific
    event_type. If no pattern matches, the event_type is set to 'custom_<level>'
    (e.g. 'custom_alert') so it's still captured but not misclassified.

    IPs are extracted from the message text using a simple regex because
    structured logs embed IPs inline rather than in a dedicated field.
    """
    m = _CUSTOM_LOG_RE.match(line)
    if not m:
        return None

    try:
        ts = datetime.strptime(f"{m.group('date')} {m.group('time')}", "%Y-%m-%d %H:%M:%S")
    except ValueError:
        ts = datetime.now()

    level     = m.group("level")
    service   = m.group("service")
    msg       = m.group("msg")
    ips       = _IP_RE.findall(msg)   # grab any IP addresses mentioned in the message
    source_ip = ips[0] if ips else None
    user      = None
    event_type = f"custom_{level.lower()}"   # fallback if no pattern matches

    for evt, pat in _CUSTOM_PATTERNS.items():
        hit = pat.search(msg)
        if not hit:
            continue
        g = hit.groups()
        if evt == "login_fail":
            user       = g[0] if g else None
            source_ip  = g[1] if len(g) > 1 else source_ip
            event_type = "ssh_fail"   # normalize to the same type detect.py expects
        elif evt in ("sqli_ids", "port_scan_ids"):
            source_ip  = g[0] if g else source_ip
            event_type = evt
        elif evt == "brute_fw":
            source_ip  = g[0] if g else source_ip
            event_type = evt
        else:
            event_type = evt
        break

    return {
        "timestamp":  ts,
        "source_ip":  source_ip,
        "user":       user,
        "event_type": event_type,
        "level":      level,
        "service":    service,
        "message":    msg,
        "raw":        line,
        "process":    service,
    }


# ── Format detection ───────────────────────────────────────────────────────────

def _detect_format(lines: list[str]) -> str:
    """Identify the log format by testing the first non-empty, non-comment lines.

    Checks up to 20 lines — enough to skip past any header comments while
    still being fast. Returns 'apache', 'syslog', 'custom', or 'unknown'.
    'unknown' triggers per-line fallback: try all three parsers in order.
    """
    for line in lines[:20]:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if _APACHE_RE.match(line):
            return "apache"
        if _SYSLOG_RE.match(line):
            return "syslog"
        if _CUSTOM_LOG_RE.match(line):
            return "custom"
    return "unknown"


# ── Public API ─────────────────────────────────────────────────────────────────

def parse_log_text(text: str) -> list[dict]:
    """Parse raw log text (any format) into a list of event dicts.

    Steps:
      1. Detect the format once from the first lines (O(1) overhead).
      2. Route each subsequent line to the matching parser.
      3. For unknown/mixed files, try all three parsers (first match wins).
      4. Skip blank lines and comments (#).

    Returns only successfully parsed lines — malformed lines are silently dropped
    because real log files contain garbage lines (kernel messages, truncations, etc.)
    and we don't want one bad line to crash the whole analysis.
    """
    lines  = text.splitlines()
    fmt    = _detect_format(lines)
    events = []

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        if fmt == "apache":
            e = _parse_apache_line(line)
        elif fmt == "syslog":
            e = _parse_syslog_line(line)
        elif fmt == "custom":
            e = _parse_custom_line(line)
        else:
            # Unknown format: try each parser, use the first that succeeds
            e = (_parse_syslog_line(line)
                 or _parse_apache_line(line)
                 or _parse_custom_line(line))

        if e:
            events.append(e)

    return events


def parse_log_file(path: str | Path) -> list[dict]:
    """Read a log file from disk and parse it. Supports .gz compressed files.

    Uses gzip.open transparently so analysts can upload compressed rotated logs
    (e.g. auth.log.gz) without needing to decompress them first.
    Returns a single error event on failure so the caller always gets a list.
    """
    path   = Path(path)
    opener = gzip.open if path.suffix == ".gz" else open
    try:
        with opener(path, "rt", encoding="utf-8", errors="replace") as f:
            return parse_log_text(f.read())
    except Exception as exc:
        # Return a parseable error event rather than raising — the dashboard
        # can display it without crashing the whole analysis run
        return [{
            "timestamp":  datetime.now(),
            "source_ip":  None,
            "user":       None,
            "event_type": "parse_error",
            "message":    str(exc),
            "raw":        "",
            "process":    "parser",
        }]
