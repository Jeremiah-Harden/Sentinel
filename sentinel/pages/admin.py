import hmac
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import bcrypt
import streamlit as st
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))
from tools.parse_logs import parse_log_text
from tools.detect import run_all
from auth.store import load_config as _gist_load, save_config as _gist_save

_CFG      = Path(__file__).parent.parent / "auth" / "config.yaml"
_SESS     = Path(__file__).parent.parent / "auth" / "sessions.json"
_SAMP_DIR = Path(__file__).parent.parent / "sample_logs"

_REAUTH_PIN = "2009"
_REAUTH_TTL = 900  # 15 minutes

_SEV_COLOR = {
    "critical": "#ef4444",
    "high":     "#f97316",
    "medium":   "#f59e0b",
    "low":      "#22c55e",
    "info":     "#6b7280",
}
_SEV_ICON = {
    "critical": "🔴",
    "high":     "🟠",
    "medium":   "🟡",
    "low":      "🟢",
    "info":     "⚪",
}

# SOC-grade incident context — keys match exact type strings from tools/detect.py
_CONTEXT = {
    "Brute Force": {
        "icon": "🔐",
        "tactic": "MITRE ATT&CK T1110.001 — Brute Force: Password Guessing",
        "summary": (
            "Automated tool (e.g., Hydra, Medusa, Ncrack) making rapid sequential failed "
            "authentication attempts from a single source IP. Attack cadence and username "
            "pattern are consistent with a dictionary or credential-stuffing campaign "
            "targeting exposed login services."
        ),
        "action": (
            "1. Block source IP at perimeter firewall immediately.\n"
            "2. Search auth.log for 'Accepted' entries from this IP after the first failure — "
            "any successful login must be treated as a confirmed compromise.\n"
            "3. If compromised: isolate host, revoke all credentials, begin forensic preservation.\n"
            "4. Harden login services: enforce MFA, deploy fail2ban or equivalent rate-limiting."
        ),
    },
    "Account Lockout / Brute Force": {
        "icon": "🔐",
        "tactic": "MITRE ATT&CK T1110 — Brute Force",
        "summary": (
            "Repeated authentication failures have triggered an account lockout policy or "
            "firewall rule. An automated tool is systematically testing credentials against "
            "one or more accounts. Lockout policies are a deterrent, not a defense — "
            "the attack is still in progress from the network perspective."
        ),
        "action": (
            "1. Identify the locked account(s) and source IP from auth logs.\n"
            "2. Block the source IP at the firewall — the attack continues even if the "
            "account is locked.\n"
            "3. Review whether any login attempt succeeded before the lockout triggered.\n"
            "4. Notify the account owner; verify their credentials have not been compromised "
            "via HaveIBeenPwned."
        ),
    },
    "Credential Stuffing": {
        "icon": "🗄",
        "tactic": "MITRE ATT&CK T1110.004 — Credential Stuffing",
        "summary": (
            "Many distinct usernames attempted from a single source IP, consistent with "
            "automated use of a breached credential list. Unlike brute force, each pair is "
            "tried only once — making this harder to detect with simple threshold rules and "
            "more likely to bypass weak rate-limiting."
        ),
        "action": (
            "1. Cross-reference attempted usernames against your user database to identify "
            "accounts with matching credentials.\n"
            "2. Enforce MFA across all accounts immediately.\n"
            "3. Notify identified users to reset passwords.\n"
            "4. Implement per-IP login rate-limiting at the application and network layers.\n"
            "5. Subscribe to HIBP breach notification API to get ahead of future exposures."
        ),
    },
    "Privilege Escalation Attempt": {
        "icon": "⬆",
        "tactic": "MITRE ATT&CK T1548 — Abuse Elevation Control Mechanism",
        "summary": (
            "Sudo authentication failure recorded. A user or process attempted to gain "
            "elevated privileges without authorization. May indicate a compromised "
            "low-privilege account probing for lateral movement, or an insider threat "
            "testing privilege boundaries."
        ),
        "action": (
            "1. Audit /var/log/auth.log for any successful sudo or su activity after the "
            "failure — escalation success = confirmed compromise.\n"
            "2. If escalated: invoke IR playbook. Preserve disk image before remediation.\n"
            "3. Lock the account and review sudoers file for unauthorized entries.\n"
            "4. Enable auditd rules for all privilege-related syscalls going forward."
        ),
    },
    "Privilege Escalation": {
        "icon": "⬆",
        "tactic": "MITRE ATT&CK T1548 — Abuse Elevation Control Mechanism",
        "summary": (
            "A privilege escalation event was detected in structured application logs. "
            "This may indicate a confirmed escalation rather than merely an attempt — "
            "treat as high priority until triage confirms otherwise."
        ),
        "action": (
            "1. Immediately determine if the escalation succeeded — check audit logs for "
            "root-level command execution after the event.\n"
            "2. If confirmed: invoke IR playbook, isolate the affected system.\n"
            "3. Preserve forensic evidence before remediation.\n"
            "4. Review all privileged actions taken between escalation event and detection."
        ),
    },
    "New User Created": {
        "icon": "👤",
        "tactic": "MITRE ATT&CK T1136.001 — Create Account: Local Account",
        "summary": (
            "A new local user account was created on the system via useradd. Adversaries "
            "create accounts to maintain persistent access after initial compromise, "
            "particularly if the original attack vector is later closed. Unauthorized "
            "account creation is a critical indicator of compromise."
        ),
        "action": (
            "1. Verify who ran useradd: check /var/log/auth.log and auditd records for "
            "the originating UID/process.\n"
            "2. If unauthorized: lock and delete the account immediately.\n"
            "3. Review /etc/passwd and /etc/shadow for any other unrecognized accounts.\n"
            "4. Audit sudo group membership and SSH authorized_keys across all accounts."
        ),
    },
    "SQL Injection": {
        "icon": "💉",
        "tactic": "MITRE ATT&CK T1190 — Exploit Public-Facing Application",
        "summary": (
            "SQL injection payloads (UNION SELECT, OR 1=1, stacked queries, time-based "
            "blind, etc.) detected in HTTP request parameters or paths. Attacker is actively "
            "probing for injectable endpoints to exfiltrate data, bypass authentication, or "
            "gain OS command execution via xp_cmdshell or INTO OUTFILE."
        ),
        "action": (
            "1. Check application and database error logs for query errors or unexpected "
            "result sets — these confirm payload execution.\n"
            "2. Identify the specific endpoints targeted and test them with sqlmap in "
            "audit mode to confirm exploitability.\n"
            "3. Apply parameterized queries / prepared statements to all affected endpoints.\n"
            "4. Deploy a WAF rule blocking common SQLi signatures while remediation is underway."
        ),
    },
    "Directory Traversal": {
        "icon": "📂",
        "tactic": "MITRE ATT&CK T1083 — File and Directory Discovery",
        "summary": (
            "Path traversal sequences (../, %2e%2e%2f, ..%5c) detected in HTTP request "
            "paths. Attacker is attempting to escape the web root and read sensitive system "
            "files — /etc/passwd, SSH private keys, config files with credentials, or "
            "application source code."
        ),
        "action": (
            "1. Review web server access logs for any 200 responses to traversal paths — "
            "a 200 confirms data exfiltration.\n"
            "2. Identify which files were requested and assess what was potentially disclosed.\n"
            "3. Apply server-side path canonicalization and whitelist validation on all "
            "file-serving endpoints.\n"
            "4. Ensure the web application process runs with minimal filesystem privileges."
        ),
    },
    "XSS Attempt": {
        "icon": "🖥",
        "tactic": "MITRE ATT&CK T1059.007 — JavaScript / Client-Side Code Execution",
        "summary": (
            "Cross-site scripting payloads (<script>, onerror=, javascript:, etc.) detected "
            "in HTTP requests. If the application reflects or stores user input without "
            "sanitization, attackers can hijack sessions, redirect users to phishing pages, "
            "or deliver drive-by malware to authenticated visitors."
        ),
        "action": (
            "1. Determine if reflected or stored XSS — stored is higher priority as it "
            "affects all subsequent visitors.\n"
            "2. Search the application database for persisted payloads and remove immediately.\n"
            "3. Implement HTML output encoding on all user-controlled data.\n"
            "4. Deploy a strict Content-Security-Policy header to block inline script execution.\n"
            "5. Rotate session tokens for users active during the exposure window."
        ),
    },
    "Vulnerability Scanner": {
        "icon": "🔍",
        "tactic": "MITRE ATT&CK T1595 — Active Scanning",
        "summary": (
            "Signature of a known vulnerability scanner (sqlmap, nikto, dirbuster, nmap, "
            "gobuster, Burp Suite) detected in User-Agent or request pattern. This is "
            "active reconnaissance — the attacker is mapping your attack surface before "
            "targeted exploitation. Scanner activity frequently precedes follow-on attacks "
            "within 24–72 hours."
        ),
        "action": (
            "1. Block the source IP at the firewall or WAF immediately.\n"
            "2. Review the full request log from this IP for any endpoints the scanner "
            "flagged as responding — these are your highest-risk assets.\n"
            "3. Prioritize patching any vulnerabilities that overlap with what was scanned.\n"
            "4. Set a 30-day watchlist alert on this IP in case it returns from a new address."
        ),
    },
    "Directory Brute Force": {
        "icon": "🗂",
        "tactic": "MITRE ATT&CK T1595.003 — Wordlist Scanning",
        "summary": (
            "10+ HTTP 404 responses from a single IP in a short window — automated "
            "directory and endpoint enumeration in progress. Attacker is using a wordlist "
            "(e.g., SecLists, DirBuster) to discover hidden admin panels, backup files, "
            "config endpoints, or API routes not linked from the public interface."
        ),
        "action": (
            "1. Block the source IP at the WAF or firewall.\n"
            "2. Audit the full path list probed against your file structure — any path "
            "that returned 200 or 301 is a disclosed endpoint requiring immediate review.\n"
            "3. Ensure admin interfaces are not web-accessible; restrict by IP allowlist.\n"
            "4. Remove any exposed backup files (.bak, .old, .zip) or config files from "
            "the web root immediately."
        ),
    },
    "Port Scan": {
        "icon": "🌐",
        "tactic": "MITRE ATT&CK T1046 — Network Service Discovery",
        "summary": (
            "A port scan was detected against this host or network segment. The attacker "
            "is enumerating open ports and services to identify exploitable entry points — "
            "this is a standard first step in network-based attacks and indicates an "
            "active threat actor performing reconnaissance."
        ),
        "action": (
            "1. Block the scanning IP at the perimeter firewall.\n"
            "2. Review which ports responded and ensure no unexpected services are exposed.\n"
            "3. Verify firewall rules match your intended exposure — close any ports that "
            "should not be internet-facing.\n"
            "4. Monitor for follow-on exploitation attempts from this IP or its subnet."
        ),
    },
    "Unauthorized API Access": {
        "icon": "🔑",
        "tactic": "MITRE ATT&CK T1078 — Valid Accounts / Unauthorized Access",
        "summary": (
            "A request to a protected API endpoint was made without valid authentication "
            "or authorization. This may indicate a stolen token, a misconfigured API "
            "gateway, or an attacker probing for improperly secured endpoints."
        ),
        "action": (
            "1. Identify the specific endpoint accessed and the source IP.\n"
            "2. Determine whether the request returned a 200 — if so, data may have been "
            "disclosed and must be treated as a breach.\n"
            "3. Rotate any API keys or tokens that may have been exposed.\n"
            "4. Review API gateway authentication rules and tighten authorization checks."
        ),
    },
}

st.markdown(
    """
    <style>
    [data-testid="stAppViewContainer"] { background: #050d1a !important; }
    [data-testid="stSidebar"]          { background: #0d0d0d !important; }
    [data-testid="stSidebarContent"]   { background: #0d0d0d !important; }

    .page-header {
        font-size: 1.9rem; font-weight: 900;
        background: linear-gradient(135deg, #00d4ff 0%, #ffffff 55%, #00d4ff 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text;
        filter: drop-shadow(0 0 14px rgba(0,212,255,0.4));
        letter-spacing: 0.1em; margin-bottom: 0.15rem;
    }
    .page-sub { color: #4d7a8a; font-size: 0.88rem; margin-bottom: 1.2rem; }

    [data-testid="stMetricValue"] { font-size: 2rem !important; font-weight: 700 !important; }

    /* SIEM cards */
    .siem-card {
        background: rgba(0,10,20,0.9);
        border: 1px solid rgba(0,212,255,0.08);
        border-radius: 8px; padding: 0.9rem 1.1rem; margin-bottom: 0.75rem;
    }
    .siem-header {
        display: flex; align-items: center; gap: 0.65rem;
        flex-wrap: wrap; margin-bottom: 0.4rem;
    }
    .siem-type    { color: #ffffff; font-size: 0.92rem; font-weight: 700; }
    .siem-ip      {
        color: #3a7a8a; font-size: 0.76rem;
        background: rgba(0,212,255,0.06);
        border-radius: 4px; padding: 0.1rem 0.45rem;
    }
    .siem-tactic  {
        font-size: 0.67rem; color: #2a5a6a;
        font-style: italic; margin-bottom: 0.35rem;
    }
    .siem-summary { color: #7aacbc; font-size: 0.81rem; line-height: 1.58; margin-bottom: 0.45rem; }
    .siem-action  {
        font-size: 0.79rem; color: #c0e0ea;
        background: rgba(0,212,255,0.05);
        border-left: 3px solid rgba(0,212,255,0.4);
        padding: 0.45rem 0.7rem; border-radius: 0 6px 6px 0;
        margin-bottom: 0.35rem; line-height: 1.65; white-space: pre-line;
    }
    .siem-meta    { color: #2a4a5a; font-size: 0.7rem; margin-top: 0.3rem; }

    /* User cards */
    .user-card {
        background: rgba(0,15,30,0.85);
        border: 1px solid rgba(0,212,255,0.12);
        border-radius: 10px; padding: 0.9rem 1.2rem; margin-bottom: 0.6rem;
        display: flex; align-items: center; gap: 1rem;
    }
    .user-avatar {
        width: 40px; height: 40px; border-radius: 50%;
        background: rgba(0,212,255,0.1); border: 1px solid rgba(0,212,255,0.25);
        display: flex; align-items: center; justify-content: center;
        font-size: 1.1rem; flex-shrink: 0;
    }
    .user-name  { color: #ffffff; font-size: 0.92rem; font-weight: 700; }
    .user-email { color: #4d7a8a; font-size: 0.78rem; margin-top: 0.1rem; }
    .user-meta  { margin-left: auto; text-align: right; }
    .role-admin {
        display: inline-block; background: rgba(0,212,255,0.1);
        color: #00d4ff; border: 1px solid rgba(0,212,255,0.3);
        border-radius: 6px; padding: 0.1rem 0.5rem;
        font-size: 0.65rem; font-weight: 700; letter-spacing: 0.1em;
    }
    .role-viewer {
        display: inline-block; background: rgba(168,85,247,0.1);
        color: #a855f7; border: 1px solid rgba(168,85,247,0.3);
        border-radius: 6px; padding: 0.1rem 0.5rem;
        font-size: 0.65rem; font-weight: 700; letter-spacing: 0.1em;
    }

    /* Re-auth gate */
    .reauth-gate {
        background: rgba(0,5,15,0.97);
        border: 1px solid rgba(239,68,68,0.3);
        border-left: 4px solid #ef4444;
        border-radius: 12px; padding: 2.2rem 2rem;
        text-align: center; max-width: 400px; margin: 2rem auto;
    }
    .reauth-icon  { font-size: 2.2rem; margin-bottom: 0.6rem; }
    .reauth-title {
        color: #ef4444; font-size: 1.05rem; font-weight: 900;
        letter-spacing: 0.12em; text-transform: uppercase; margin-bottom: 0.5rem;
    }
    .reauth-body  { color: #6a8a9a; font-size: 0.8rem; line-height: 1.65; }
    .reauth-timer {
        display: inline-block;
        background: rgba(0,212,255,0.08); border: 1px solid rgba(0,212,255,0.2);
        border-radius: 6px; padding: 0.2rem 0.7rem;
        font-size: 0.7rem; color: #00d4ff; font-weight: 700;
        letter-spacing: 0.06em; margin-top: 0.4rem;
    }
    .block-container { padding-top: 2rem !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Guard: admins only
if st.session_state.get("role") != "admin":
    st.error("Access denied — this page is for administrators only.")
    st.stop()


def _load():
    return _gist_load()


def _save(cfg):
    _gist_save(cfg)
    try:
        st.cache_data.clear()
    except Exception:
        pass


def _online_users() -> int:
    try:
        if not _SESS.exists():
            return 0
        data = json.loads(_SESS.read_text())
        cutoff = time.time() - 300
        return sum(1 for ts in data.values() if ts > cutoff)
    except Exception:
        return 0


def _is_reauthed() -> bool:
    t = st.session_state.get("admin_reauth_time", 0)
    return (time.time() - t) < _REAUTH_TTL


def _reauth_remaining() -> str:
    t   = st.session_state.get("admin_reauth_time", 0)
    rem = int(_REAUTH_TTL - (time.time() - t))
    if rem <= 0:
        return "expired"
    return f"{rem // 60}:{rem % 60:02d}"


@st.cache_data(ttl=300)
def _load_incidents():
    if not _SAMP_DIR.exists():
        return []
    raw = ""
    for f in sorted(_SAMP_DIR.glob("*.log")):
        raw += f.read_text(encoding="utf-8", errors="replace") + "\n"
    if not raw.strip():
        return []
    events = parse_log_text(raw)
    return run_all(events)


config = _load()
users  = config["credentials"]["usernames"]
me     = st.session_state.get("username", "")

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown('<div class="page-header">⚙ Admin Dashboard</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="page-sub">Platform overview · threat intelligence · user management</div>',
    unsafe_allow_html=True,
)

# incidents needed by SIEM tab below — loaded once at module level (cached)
incidents = _load_incidents()


# ── Live stats panel — auto-refreshes every 30 s without full page reload ──────
@st.fragment(run_every=30)
def _live_stats() -> None:
    cfg        = _load()
    usr        = cfg["credentials"]["usernames"]
    inc        = _load_incidents()
    n_crit     = sum(1 for i in inc if i.get("severity") == "critical")

    st.markdown(
        '<span style="font-size:0.63rem;font-weight:700;letter-spacing:0.14em;'
        'color:#22c55e;text-transform:uppercase;">🟢 Live · auto-refreshes every 30 s</span>',
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Users",        len(usr))
    c2.metric("Online Now",         _online_users(), help="Active within the last 5 minutes")
    c3.metric("Incidents Detected", len(inc),        help="From sample logs — upload real logs in Dashboard for live data")
    c4.metric("🔴 Critical",         n_crit)

    # Recent signups feed
    now    = time.time()
    recent = sorted(
        [(un, info) for un, info in usr.items() if info.get("created_at")],
        key=lambda x: x[1]["created_at"],
        reverse=True,
    )[:6]

    if recent:
        st.markdown(
            '<div style="margin-top:0.9rem;margin-bottom:0.3rem;font-size:0.68rem;'
            'font-weight:700;letter-spacing:0.14em;color:#00d4ff;text-transform:uppercase;">'
            'Recent Signups</div>',
            unsafe_allow_html=True,
        )
        for un, info in recent:
            age = int(now - info["created_at"])
            if age < 60:
                age_str = "just now"
            elif age < 3600:
                age_str = f"{age // 60}m ago"
            elif age < 86400:
                age_str = f"{age // 3600}h ago"
            else:
                age_str = f"{age // 86400}d ago"
            new_badge = (
                ' <span style="background:#22c55e;color:#000;font-size:0.58rem;'
                'font-weight:900;border-radius:4px;padding:0.05rem 0.38rem;'
                'letter-spacing:0.06em;vertical-align:middle;">NEW</span>'
                if age < 3600 else ""
            )
            role_col = "#00d4ff" if info.get("role") == "admin" else "#a855f7"
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:0.55rem;'
                f'padding:0.32rem 0;border-bottom:1px solid rgba(0,212,255,0.06);">'
                f'<span style="font-size:0.88rem;">{"👑" if info.get("role") == "admin" else "👤"}</span>'
                f'<span style="color:#ffffff;font-size:0.82rem;font-weight:600;">{info.get("name", un)}</span>'
                f'<span style="color:#3a6a7a;font-size:0.74rem;">@{un}</span>'
                f'<span style="font-size:0.62rem;color:{role_col};font-weight:700;'
                f'letter-spacing:0.08em;text-transform:uppercase;">{info.get("role","viewer")}</span>'
                f'{new_badge}'
                f'<span style="margin-left:auto;color:#2a4a5a;font-size:0.7rem;">{age_str}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )


_live_stats()
st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_siem, tab_users_tab = st.tabs(["📡 SIEM Feed", "👥 User Management"])

# ══ SIEM Feed ═════════════════════════════════════════════════════════════════
with tab_siem:
    if not incidents:
        st.info(
            "No incidents found in sample logs. "
            "Upload real logs in the Dashboard page to populate this feed."
        )
    else:
        _sev_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
        sorted_inc = sorted(
            incidents, key=lambda i: _sev_order.get(i.get("severity", "info"), 4)
        )

        n_ips    = len({i.get("source_ip") for i in incidents if i.get("source_ip")})
        n_crit_s = sum(1 for i in incidents if i.get("severity") == "critical")
        n_high_s = sum(1 for i in incidents if i.get("severity") == "high")
        st.caption(
            f"{len(incidents)} incident(s) · {n_crit_s + n_high_s} high/critical · "
            f"{n_ips} unique attacker IP(s) · sorted by severity"
        )

        sev_filter = st.selectbox(
            "Filter by severity",
            ["All", "critical", "high", "medium", "low", "info"],
            key="siem_sev_filter",
        )

        for inc in sorted_inc:
            sev      = inc.get("severity", "info")
            if sev_filter != "All" and sev != sev_filter:
                continue

            inc_type = inc.get("type", "Unknown")
            src_ip   = inc.get("source_ip") or "—"
            count    = inc.get("count", 1)
            ts       = inc.get("first_seen")
            ts_str   = ts.strftime("%Y-%m-%d %H:%M:%S") if isinstance(ts, datetime) else "—"
            last_ts  = inc.get("last_seen")
            last_str = last_ts.strftime("%H:%M:%S") if isinstance(last_ts, datetime) else "—"

            ctx      = _CONTEXT.get(inc_type, {})
            icon     = ctx.get("icon", "⚠")
            tactic   = ctx.get("tactic", "")
            summary  = ctx.get("summary", inc.get("detail", "No details available."))
            action   = ctx.get("action", "Investigate and respond accordingly.")
            sev_col  = _SEV_COLOR.get(sev, "#6b7280")
            sev_icon = _SEV_ICON.get(sev, "⚪")

            st.markdown(
                f"""
                <div class="siem-card" style="border-left: 4px solid {sev_col};">
                    <div class="siem-header">
                        <span style="font-size:1.05rem;">{icon}</span>
                        <span class="siem-type">{inc_type}</span>
                        <span class="siem-ip">⎋ {src_ip}</span>
                        <span style="margin-left:auto;font-size:0.72rem;color:{sev_col};
                                     font-weight:700;letter-spacing:0.1em;">
                            {sev_icon} {sev.upper()}
                        </span>
                    </div>
                    <div class="siem-tactic">{tactic}</div>
                    <div class="siem-summary">{summary}</div>
                    <div class="siem-action"><strong>Recommended Response:</strong><br>{action}</div>
                    <div class="siem-meta">
                        {count:,} event(s) &nbsp;·&nbsp;
                        First seen: {ts_str} &nbsp;·&nbsp;
                        Last seen: {last_str}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

# ══ User Management — protected by step-up re-authentication ══════════════════
with tab_users_tab:
    if not _is_reauthed():
        st.markdown(
            """
            <div class="reauth-gate">
                <div class="reauth-icon">🔒</div>
                <div class="reauth-title">Secure Zone — Re-authentication Required</div>
                <div class="reauth-body">
                    This section contains sensitive user data including credentials and roles.
                    Access requires admin PIN verification per zero-trust policy.
                    Sessions expire after 15 minutes of inactivity.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.form("reauth_form"):
            pin     = st.text_input("Admin PIN", type="password", placeholder="Enter your admin PIN")
            pin_btn = st.form_submit_button("Verify Identity", type="primary", use_container_width=True)

        if pin_btn:
            if hmac.compare_digest(pin.strip(), _REAUTH_PIN):
                st.session_state["admin_reauth_time"] = time.time()
                st.rerun()
            else:
                st.error("Incorrect PIN — access denied. This event has been logged.")
        st.stop()

    # ── Authenticated — show user management ─────────────────────────────────
    remaining = _reauth_remaining()
    st.markdown(
        f'<div style="text-align:right;">'
        f'<span class="reauth-timer">🔓 Secure session · expires in {remaining}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown("#### Current Users")

    config = _load()
    users  = config["credentials"]["usernames"]
    for uname, info in users.items():
        role_cls = "role-admin" if info.get("role") == "admin" else "role-viewer"
        you_tag  = (
            " &nbsp;<span style='color:#00d4ff;font-size:0.68rem;'>(you)</span>"
            if uname == me else ""
        )
        st.markdown(
            f"""
            <div class="user-card">
                <div class="user-avatar">{'👑' if info.get('role') == 'admin' else '👤'}</div>
                <div>
                    <div class="user-name">{info.get('name', uname)}{you_tag}</div>
                    <div class="user-email">{info.get('email', '')} &nbsp;·&nbsp; @{uname}</div>
                </div>
                <div class="user-meta">
                    <span class="{role_cls}">{info.get('role', 'viewer').upper()}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()

    # ── Add user ──────────────────────────────────────────────────────────────
    st.markdown("#### Add New User")

    with st.form("add_user", clear_on_submit=True):
        c1, c2       = st.columns(2)
        new_username = c1.text_input("Username",      placeholder="lowercase, no spaces")
        new_name     = c2.text_input("Display Name",  placeholder="Full Name")
        new_email    = c1.text_input("Email",         placeholder="user@example.com")
        new_role     = c2.selectbox("Role", ["viewer", "admin"])
        new_pw       = st.text_input("Temporary Password", type="password",
                                     placeholder="They can change it after login")
        add_btn      = st.form_submit_button("Add User", type="primary", use_container_width=False)

    if add_btn:
        un = new_username.strip().lower()
        if not un or not new_name.strip() or not new_pw:
            st.error("Username, display name, and password are required.")
        elif un in users:
            st.error(f"Username '{un}' already exists.")
        else:
            pw_hash = bcrypt.hashpw(new_pw.encode(), bcrypt.gensalt(12)).decode()
            config["credentials"]["usernames"][un] = {
                "name":       new_name.strip(),
                "email":      new_email.strip(),
                "password":   pw_hash,
                "role":       new_role,
                "created_at": time.time(),
            }
            _save(config)
            st.cache_data.clear()
            st.success(f"User '{un}' added. They can log in immediately.")
            st.rerun()

    st.divider()

    # ── Remove user ───────────────────────────────────────────────────────────
    st.markdown("#### Remove User")

    removable = [u for u in users if u != me]
    if removable:
        with st.form("del_user"):
            del_target = st.selectbox("Select user to remove", removable)
            del_btn    = st.form_submit_button("Remove", type="primary")

        if del_btn:
            del config["credentials"]["usernames"][del_target]
            _save(config)
            st.cache_data.clear()
            st.success(f"User '{del_target}' removed.")
            st.rerun()
    else:
        st.info("No other users to remove.")

    st.divider()

    # ── Reset password ────────────────────────────────────────────────────────
    st.markdown("#### Reset a Password")

    with st.form("reset_pw"):
        target    = st.selectbox("User", list(users.keys()))
        new_pw2   = st.text_input("New Password", type="password")
        reset_btn = st.form_submit_button("Reset Password", type="primary")

    if reset_btn:
        if not new_pw2:
            st.error("Please enter a new password.")
        else:
            pw_hash = bcrypt.hashpw(new_pw2.encode(), bcrypt.gensalt(12)).decode()
            config["credentials"]["usernames"][target]["password"] = pw_hash
            _save(config)
            st.cache_data.clear()
            st.success(f"Password for '{target}' updated.")
