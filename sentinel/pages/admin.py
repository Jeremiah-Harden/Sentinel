from pathlib import Path

import bcrypt
import streamlit as st
import yaml

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
    .page-sub { color: #4d7a8a; font-size: 0.88rem; margin-bottom: 1.5rem; }

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
    .role-admin  {
        display:inline-block; background:rgba(0,212,255,0.1);
        color:#00d4ff; border:1px solid rgba(0,212,255,0.3);
        border-radius:6px; padding:0.1rem 0.5rem;
        font-size:0.65rem; font-weight:700; letter-spacing:0.1em;
    }
    .role-viewer {
        display:inline-block; background:rgba(168,85,247,0.1);
        color:#a855f7; border:1px solid rgba(168,85,247,0.3);
        border-radius:6px; padding:0.1rem 0.5rem;
        font-size:0.65rem; font-weight:700; letter-spacing:0.1em;
    }
    .block-container { padding-top: 2rem !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Guard: only admins can access this page
if st.session_state.get("role") != "admin":
    st.error("Access denied — this page is for administrators only.")
    st.stop()

_CFG = Path(__file__).parent.parent / "auth" / "config.yaml"


def _load():
    with open(_CFG) as f:
        return yaml.safe_load(f)


def _save(cfg):
    with open(_CFG, "w") as f:
        yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True)


st.markdown('<div class="page-header">👥 User Management</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">Manage who can access Sentinel</div>', unsafe_allow_html=True)

config = _load()
users  = config["credentials"]["usernames"]
me     = st.session_state.get("username", "")

# ── Current users ─────────────────────────────────────────────────────────────
st.markdown("#### Current Users")

for uname, info in users.items():
    role_cls = "role-admin" if info.get("role") == "admin" else "role-viewer"
    you_tag  = " &nbsp;<span style='color:#00d4ff;font-size:0.68rem;'>(you)</span>" if uname == me else ""
    st.markdown(
        f"""
        <div class="user-card">
            <div class="user-avatar">{'👑' if info.get('role')=='admin' else '👤'}</div>
            <div>
                <div class="user-name">{info.get('name', uname)}{you_tag}</div>
                <div class="user-email">{info.get('email', '')} &nbsp;·&nbsp; @{uname}</div>
            </div>
            <div class="user-meta">
                <span class="{role_cls}">{info.get('role','viewer').upper()}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()

# ── Add user ──────────────────────────────────────────────────────────────────
st.markdown("#### Add New User")

with st.form("add_user", clear_on_submit=True):
    c1, c2 = st.columns(2)
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
        st.info("To make this permanent on the live site, commit and push auth/config.yaml to GitHub.")
        st.rerun()

st.divider()

# ── Delete user ───────────────────────────────────────────────────────────────
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
        st.info("Commit and push auth/config.yaml to apply on the live site.")
        st.rerun()
else:
    st.info("No other users to remove.")

st.divider()

# ── Reset password ────────────────────────────────────────────────────────────
st.markdown("#### Reset a Password")

with st.form("reset_pw"):
    target = st.selectbox("User", list(users.keys()))
    new_pw2 = st.text_input("New Password", type="password")
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
        st.info("Commit and push auth/config.yaml to apply on the live site.")
