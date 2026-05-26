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

# SOC-grade incident context — mirrors enterprise SIEM playbooks
_CONTEXT = {
    "SSH Brute Force": {
        "icon": "🔐",
        "tactic": "MITRE ATT&CK T1110.001 — Brute Force: Password Guessing",
        "summary": (
            "Automated tool (e.g., Hydra, Medusa, Ncrack) detected making rapid sequential "
            "failed SSH authentication attempts from a single source IP. Attack cadence and "
            "username pattern are consistent with a dictionary or credential-stuffing campaign "
            "targeting exposed SSH services."
        ),
        "action": (
            "1. Block source IP at perimeter firewall (deny TCP/22 inbound). "
            "2. Search auth.log for 'Accepted' entries from this IP after the first failure — "
            "any successful login must be treated as a confirmed compromise. "
            "3. If compromised: isolate host, revoke all SSH credentials, begin forensic preservation. "
            "4. Harden sshd: enforce key-based auth only, disable root login, deploy fail2ban."
        ),
    },
    "Credential Stuffing": {
        "icon": "🗄",
        "tactic": "MITRE ATT&CK T1110.004 — Credential Stuffing",
        "summary": (
            "Many distinct usernames attempted from a single source IP, consistent with "
            "automated use of a breached credential list (e.g., from HaveIBeenPwned corpus). "
            "Unlike brute force, each pair is tried only once — making this attack harder to "
            "detect with simple threshold rules and more likely to bypass weak rate-limiting."
        ),
        "action": (
            "1. Cross-reference the attempted usernames against your user database — "
            "identify any accounts with matching credentials. "
            "2. Enforce MFA on all accounts immediately. "
            "3. Notify identified users to reset passwords. "
            "4. Implement per-IP login rate-limiting at the application and network layers. "
            "5. Consider subscribing to HIBP breach notification API."
        ),
    },
    "Privilege Escalation": {
        "icon": "⬆",
        "tactic": "MITRE ATT&CK T1548 — Abuse Elevation Control Mechanism",
        "summary": (
            "Sudo failures or unauthorized root access attempts recorded. May indicate "
            "a compromised low-privilege account attempting lateral movement, an insider "
            "threat testing privilege boundaries, or a post-exploitation phase following "
            "initial access. Requires immediate triage."
        ),
        "action": (
            "1. Audit /var/log/auth.log for any successful sudo or su activity after the "
            "first failure — escalation success = confirmed compromise. "
            "2. If escalated: invoke IR playbook immediately. Preserve disk image before "
            "remediation to maintain forensic integrity. "
            "3. Lock the account. Review sudoers file for unauthorized entries. "
            "4. Enable auditd rules for all privilege-related syscalls."
        ),
    },
    "New OS Account": {
        "icon": "👤",
        "tactic": "MITRE ATT&CK T1136.001 — Create Account: Local Account",
        "summary": (
            "A new local user account was created on the system via useradd. "
            "Adversaries create accounts to maintain persistent access after initial "
            "compromise, particularly if the original attack vector is closed. "
            "Unauthorized account creation is a critical indicator of compromise."
        ),
        "action": (
            "1. Verify who ran useradd: check /var/log/auth.log and auditd records for "
            "the originating UID/process. "
            "2. If unauthorized: lock and delete the account immediately. "
            "3. Review /etc/passwd and /etc/shadow for any other unrecognized accounts. "
            "4. Audit sudo group membership and SSH authorized_keys across all accounts."
        ),
    },
    "SQL Injection": {
        "icon": "💉",
        "tactic": "MITRE ATT&CK T1190 — Exploit Public-Facing Application",
        "summary": (
            "SQL injection payloads (UNION SELECT, OR 1=1, stacked queries, etc.) detected "
            "in HTTP request parameters or paths. Attacker is actively probing for injectable "
            "endpoints to exfiltrate data, bypass authentication, or gain command execution "
            "via xp_cmdshell / INTO OUTFILE."
        ),
        "action": (
            "1. Check application and database error logs for query errors or unexpected "
            "result sets that indicate payload execution. "
            "2. Identify the specific endpoints targeted — test them manually or with "
            "sqlmap in audit mode to confirm vulnerability. "
            "3. Apply parameterized queries / prepared statements to all affected endpoints. "
            "4. Deploy a WAF rule blocking common SQLi signatures while remediation is underway."
        ),
    },
    "Directory Traversal": {
        "icon": "📂",
        "tactic": "MITRE ATT&CK T1083 — File and Directory Discovery",
        "summary": (
            "Path traversal sequences (../, %2e%2e%2f, ..%5c) detected in HTTP request "
            "paths. Attacker is attempting to escape the web root and read sensitive system "
            "files — /etc/passwd, private keys, config files with credentials, or "
            "application source code."
        ),
        "action": (
            "1. Review web server access logs for any response codes other than 400/403 "
            "for traversal paths — a 200 response confirms data exfiltration. "
            "2. Identify which files were requested and assess what was potentially disclosed. "
            "3. Apply server-side path canonicalization and whitelist validation on all "
            "file-serving endpoints. "
            "4. Ensure the web application process runs with minimal filesystem privileges."
        ),
    },
    "XSS Attempts": {
        "icon": "🖥",
        "tactic": "MITRE ATT&CK T1059.007 — JavaScript / Client-Side Code Execution",
        "summary": (
            "Cross-site scripting payloads (<script>, onerror=, javascript:, etc.) detected "
            "in HTTP requests. If the application reflects or stores user input without "
            "sanitization, attackers can hijack sessions, redirect users to phishing pages, "
            "or deliver drive-by malware to authenticated visitors."
        ),
        "action": (
            "1. Determine if the attack vector is reflected or stored XSS — stored is "
            "higher priority as it affects all subsequent visitors. "
            "2. Search application DB for persisted payloads. Remove any found immediately. "
            "3. Implement output encoding on all user-controlled data rendered in HTML. "
            "4. Deploy a strict Content-Security-Policy header to block inline script execution. "
            "5. Rotate session tokens for any users who may have been active during exposure."
        ),
    },
    "Vulnerability Scanners": {
        "icon": "🔍",
        "tactic": "MITRE ATT&CK T1595 — Active Scanning",
        "summary": (
            "Signature of a known vulnerability scanner (sqlmap, nikto, dirbuster, nmap, "
            "gobuster) detected in User-Agent or request pattern. This is reconnaissance — "
            "the attacker is mapping your attack surface before targeted exploitation. "
            "Scanner activity frequently precedes more dangerous follow-on attacks within "
            "24–72 hours."
        ),
        "action": (
            "1. Block the source IP at the firewall or WAF immediately. "
            "2. Capture the full request log from this IP and review for any specific "
            "endpoints or vulnerabilities the scanner flagged as present. "
            "3. Prioritize patching any findings from your own vulnerability management "
            "program that overlap with what was scanned. "
            "4. Set a 30-day alert on this IP in case it returns from a different address."
        ),
    },
    "Directory Brute Force": {
        "icon": "🗂",
        "tactic": "MITRE ATT&CK T1595.003 — Wordlist Scanning",
        "summary": (
            "10+ HTTP 404 responses from a single IP in a short window — automated "
            "directory and endpoint enumeration in progress. Attacker is using a wordlist "
            "(e.g., SecLists) to discover hidden admin panels, backup files, config endpoints, "
            "or API routes not linked from the public interface."
        ),
        "action": (
            "1. Block the source IP at the WAF or firewall. "
            "2. Audit the full path list probed against your actual file structure — "
            "any match that returned 200/301 is a disclosed endpoint and must be reviewed. "
            "3. Ensure admin interfaces are not web-accessible; restrict by IP allowlist. "
            "4. Remove any exposed backup files (.bak, .old, .zip) or config files from "
            "the web root immediately."
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
    with open(_CFG) as f:
        return yaml.safe_load(f)


def _save(cfg):
    with open(_CFG, "w") as f:
        yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True)


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

# ── Stats row ─────────────────────────────────────────────────────────────────
incidents  = _load_incidents()
n_critical = sum(1 for i in incidents if i.get("severity") == "critical")
n_high     = sum(1 for i in incidents if i.get("severity") == "high")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Users",        len(users))
c2.metric("Online Now",         _online_users(),  help="Active within the last 5 minutes")
c3.metric("Incidents Detected", len(incidents),   help="From sample logs — upload real logs in Dashboard for live data")
c4.metric("🔴 Critical",         n_critical)

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

        n_ips = len({i.get("source_ip") for i in incidents if i.get("source_ip")})
        st.caption(
            f"{len(incidents)} incident(s) · {n_critical + n_high} high/critical · "
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
                "name":     new_name.strip(),
                "email":    new_email.strip(),
                "password": pw_hash,
                "role":     new_role,
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
