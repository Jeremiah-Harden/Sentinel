import re
import gzip
from datetime import datetime
from pathlib import Path

_MONTH = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
}

_SYSLOG_RE = re.compile(
    r"^(?P<month>\w{3})\s{1,2}(?P<day>\d+)\s(?P<time>\d{2}:\d{2}:\d{2})\s"
    r"(?P<host>\S+)\s(?P<proc>[^\[:]+)(?:\[(?P<pid>\d+)\])?:\s*(?P<msg>.+)$"
)

_APACHE_RE = re.compile(
    r"^(?P<ip>\S+)\s+\S+\s+\S+\s+\[(?P<time>[^\]]+)\]\s+"
    r'"(?P<method>[A-Z]+)\s+(?P<path>\S+)\s+\S+"\s+(?P<status>\d+)\s+(?P<size>\S+)'
    r'(?:\s+"(?P<referer>[^"]*)"\s+"(?P<ua>[^"]*)")?'
)

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

_SQLI_RE = re.compile(
    r"(?i)(union\s+select|select\s+.+\s+from|insert\s+into|drop\s+table|"
    r"exec\s*\(|xp_cmdshell|'--|%27--|or\s+1=1|and\s+1=1|"
    r"information_schema|sysobjects|syscolumns)"
)
_TRAVERSAL_RE = re.compile(r"\.\.\/|\.\.\\|%2e%2e%2f|%252e", re.I)
_XSS_RE = re.compile(r"(?i)(<script|javascript:|onerror=|onload=|alert\s*\()")
_SCANNER_UA_RE = re.compile(
    r"(?i)(sqlmap|nikto|nmap|masscan|dirbuster|gobuster|wfuzz|burpsuite|"
    r"acunetix|nessus|openvas|w3af|skipfish|havij|zgrab)"
)

# ── Custom app log format: "YYYY-MM-DD HH:MM:SS LEVEL [service] message" ──────
_CUSTOM_LOG_RE = re.compile(
    r"^(?P<date>\d{4}-\d{2}-\d{2})\s+(?P<time>\d{2}:\d{2}:\d{2})\s+"
    r"(?P<level>INFO|WARN|ERROR|ALERT|DEBUG|CRITICAL)\s+\[(?P<service>[^\]]+)\]\s+(?P<msg>.+)$"
)
_IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")

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


def _syslog_ts(m) -> datetime:
    year = datetime.now().year
    mon  = _MONTH.get(m.group("month"), 1)
    day  = int(m.group("day"))
    h, mi, s = (int(x) for x in m.group("time").split(":"))
    return datetime(year, mon, day, h, mi, s)


def _apache_ts(s: str) -> datetime:
    try:
        return datetime.strptime(s[:20], "%d/%b/%Y:%H:%M:%S")
    except ValueError:
        return datetime.now()


def _parse_syslog_line(line: str) -> dict | None:
    m = _SYSLOG_RE.match(line)
    if not m:
        return None
    msg  = m.group("msg")
    proc = m.group("proc").strip()
    ts   = _syslog_ts(m)
    base = {
        "timestamp": ts, "source_ip": None, "user": None,
        "event_type": "syslog", "message": msg, "raw": line, "process": proc,
    }
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
        break
    return base


def _parse_apache_line(line: str) -> dict | None:
    m = _APACHE_RE.match(line)
    if not m:
        return None
    ip     = m.group("ip")
    ts     = _apache_ts(m.group("time"))
    method = m.group("method")
    path   = m.group("path")
    status = int(m.group("status"))
    ua     = m.group("ua") or ""

    evt = "web_request"
    if _SQLI_RE.search(path):
        evt = "sqli_attempt"
    elif _TRAVERSAL_RE.search(path):
        evt = "traversal_attempt"
    elif _XSS_RE.search(path):
        evt = "xss_attempt"
    elif _SCANNER_UA_RE.search(ua):
        evt = "scanner_detected"
    elif status == 404 and method == "GET":
        evt = "web_404"
    elif status >= 500:
        evt = "web_error"

    return {
        "timestamp": ts, "source_ip": ip, "user": None,
        "event_type": evt, "status_code": status,
        "method": method, "path": path, "user_agent": ua,
        "message": f"{method} {path} → {status}", "raw": line, "process": "httpd",
    }


def _parse_custom_line(line: str) -> dict | None:
    m = _CUSTOM_LOG_RE.match(line)
    if not m:
        return None
    try:
        ts = datetime.strptime(f"{m.group('date')} {m.group('time')}", "%Y-%m-%d %H:%M:%S")
    except ValueError:
        ts = datetime.now()

    level      = m.group("level")
    service    = m.group("service")
    msg        = m.group("msg")
    ips        = _IP_RE.findall(msg)
    source_ip  = ips[0] if ips else None
    user       = None
    event_type = f"custom_{level.lower()}"

    for evt, pat in _CUSTOM_PATTERNS.items():
        hit = pat.search(msg)
        if not hit:
            continue
        g = hit.groups()
        if evt == "login_fail":
            user       = g[0] if g else None
            source_ip  = g[1] if len(g) > 1 else source_ip
            event_type = "ssh_fail"
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


def _detect_format(lines: list[str]) -> str:
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


def parse_log_text(text: str) -> list[dict]:
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
            e = (_parse_syslog_line(line)
                 or _parse_apache_line(line)
                 or _parse_custom_line(line))
        if e:
            events.append(e)
    return events


def parse_log_file(path: str | Path) -> list[dict]:
    path   = Path(path)
    opener = gzip.open if path.suffix == ".gz" else open
    try:
        with opener(path, "rt", encoding="utf-8", errors="replace") as f:
            return parse_log_text(f.read())
    except Exception as exc:
        return [{
            "timestamp": datetime.now(), "source_ip": None, "user": None,
            "event_type": "parse_error", "message": str(exc), "raw": "", "process": "parser",
        }]
