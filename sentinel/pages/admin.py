import sys
import json
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

_CONTEXT = {
    "SSH Brute Force": {
        "icon": "🔐",
        "summary": "Multiple failed SSH logins from one IP in a short window — automated credential stuffing attack.",
        "action": "Block the source IP in your firewall. Check auth.log for any successful login that followed the failures.",
    },
    "Credential Stuffing": {
        "icon": "🗄",
        "summary": "Many different usernames tried from a single IP — attacker is using a leaked credential database.",
        "action": "Enforce MFA across all accounts. Audit recent successful logins from this IP.",
    },
    "Privilege Escalation": {
        "icon": "⬆",
        "summary": "Sudo failures or unauthorized root access attempts — someone is trying to gain elevated privileges.",
        "action": "Review /var/log/auth.log immediately. Determine if escalation succeeded and lock the account if compromised.",
    },
    "New OS Account": {
        "icon": "👤",
        "summary": "A new user account was created on the system via useradd.",
        "action": "Verify this was authorized by an admin. If unexpected, disable immediately and investigate who ran useradd.",
    },
    "SQL Injection": {
        "icon": "💉",
        "summary": "SQL injection payloads detected in HTTP request paths — attacker probing for database vulnerabilities.",
        "action": "Check if any payloads reached the database layer. Apply input sanitization and parameterized queries.",
    },
    "Directory Traversal": {
        "icon": "📂",
        "summary": "Path traversal patterns (../) in HTTP requests — attacker attempting to read files outside the web root.",
        "action": "Sanitize all file path inputs server-side. Review what paths were requested and whether any returned 200.",
    },
    "XSS Attempts": {
        "icon": "🖥",
        "summary": "Cross-site scripting payloads in web requests — attacker trying to inject malicious scripts.",
        "action": "Check if any payloads were reflected or stored. Implement Content Security Policy (CSP) headers.",
    },
    "Vulnerability Scanners": {
        "icon": "🔍",
        "summary": "Known scanner signature detected (sqlmap, nikto, nmap, dirbuster) — active reconnaissance in progress.",
        "action": "Log the source IP and monitor for follow-up exploitation attempts. Consider blocking at the firewall.",
    },
    "Directory Brute Force": {
        "icon": "🗂",
        "summary": "10+ 404 errors from one IP in a short window — automated scan for hidden directories and endpoints.",
        "action": "Block the source IP. Review the path list probed for anything sensitive that might actually exist.",
    },
}

st.markdown(
    """
    <style>
    [data-testid="stAppViewContainer"] { background: #050d1a !important; }
    [data-testid="stSidebar"]          { background: #0d0d0d !important; }
    [data-testid="stSidebarContent"]   { background: #0d0d0d !important; }

    .page-header {
        font-size: 1.9rem;
        font-weight: 900;
        background: linear-gradient(135deg, #00d4ff 0%, #ffffff 55%, #00d4ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        filter: drop-shadow(0 0 14px rgba(0,212,255,0.4));
        letter-spacing: 0.1em;
        margin-bottom: 0.15rem;
    }
    .page-sub { color: #4d7a8a; font-size: 0.88rem; margin-bottom: 1.2rem; }

    [data-testid="stMetricValue"] { font-size: 2rem !important; font-weight: 700 !important; }

    /* SIEM incident cards */
    .siem-card {
        background: rgba(0,10,20,0.9);
        border: 1px solid rgba(0,212,255,0.08);
        border-radius: 8px;
        padding: 0.9rem 1.1rem;
        margin-bottom: 0.7rem;
    }
    .siem-header {
        display: flex;
        align-items: center;
        gap: 0.65rem;
        flex-wrap: wrap;
        margin-bottom: 0.45rem;
    }
    .siem-type    { color: #ffffff; font-size: 0.92rem; font-weight: 700; }
    .siem-ip      {
        color: #3a7a8a; font-size: 0.76rem;
        background: rgba(0,212,255,0.06);
        border-radius: 4px; padding: 0.1rem 0.45rem;
    }
    .siem-summary { color: #7aacbc; font-size: 0.82rem; line-height: 1.55; margin-bottom: 0.4rem; }
    .siem-action  {
        font-size: 0.8rem; color: #00d4ff;
        background: rgba(0,212,255,0.06);
        border-left: 2px solid rgba(0,212,255,0.45);
        padding: 0.3rem 0.65rem;
        border-radius: 0 5px 5px 0;
        margin-bottom: 0.35rem;
    }
    .siem-meta    { color: #2a4a5a; font-size: 0.7rem; margin-top: 0.3rem; }

    /* User cards */
    .user-card {
        background: rgba(0,15,30,0.85);
        border: 1px solid rgba(0,212,255,0.12);
        border-radius: 10px;
        padding: 0.9rem 1.2rem;
        margin-bottom: 0.6rem;
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    .user-avatar {
        width: 40px; height: 40px;
        border-radius: 50%;
        background: rgba(0,212,255,0.1);
        border: 1px solid rgba(0,212,255,0.25);
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
        cutoff = time.time() - 300  # active within last 5 minutes
        return sum(1 for ts in data.values() if ts > cutoff)
    except Exception:
        return 0


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
c2.metric("Online Now",         _online_users(),   help="Active within the last 5 minutes")
c3.metric("Incidents Detected", len(incidents),    help="Analyzed from sample logs — upload real logs in Dashboard for live data")
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

        n_high_total = n_critical + n_high
        st.caption(
            f"{len(incidents)} incident(s) detected · "
            f"{n_high_total} high/critical · "
            f"{len({i.get('source_ip') for i in incidents if i.get('source_ip')})} unique attacker IPs"
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
                    <div class="siem-summary">{summary}</div>
                    <div class="siem-action">
                        ⚡ <strong>Recommended action:</strong> {action}
                    </div>
                    <div class="siem-meta">
                        {count:,} event(s) &nbsp;·&nbsp;
                        First seen: {ts_str} &nbsp;·&nbsp;
                        Last seen: {last_str}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

# ══ User Management ═══════════════════════════════════════════════════════════
with tab_users_tab:
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
        new_username = c1.text_input("Username", placeholder="lowercase, no spaces")
        new_name     = c2.text_input("Display Name", placeholder="Full Name")
        new_email    = c1.text_input("Email", placeholder="user@example.com")
        new_role     = c2.selectbox("Role", ["viewer", "admin"])
        new_pw       = st.text_input("Temporary Password", type="password", placeholder="They can change it after login")
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
