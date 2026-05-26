import base64
from pathlib import Path

import bcrypt
import streamlit as st
import yaml

st.set_page_config(
    page_title="Sentinel",
    page_icon="🛡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Auth helpers ───────────────────────────────────────────────────────────────
_CFG_PATH = Path(__file__).parent / "auth" / "config.yaml"


@st.cache_data(ttl=60)
def _load_config():
    with open(_CFG_PATH) as f:
        return yaml.safe_load(f)


def _check_password(username: str, password: str, config: dict) -> bool:
    user = config["credentials"]["usernames"].get(username.lower())
    if not user:
        return False
    return bcrypt.checkpw(password.encode(), user["password"].encode())


def _user_info(username: str, config: dict) -> dict:
    return config["credentials"]["usernames"].get(username.lower(), {})


def _save_config(config: dict) -> None:
    with open(_CFG_PATH, "w") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
    st.cache_data.clear()


# ── Image helper ───────────────────────────────────────────────────────────────
def _img_b64(name: str) -> str:
    p = Path(__file__).parent / "assets" / name
    try:
        ext = p.suffix.lstrip(".")
        return f"data:image/{ext};base64," + base64.b64encode(p.read_bytes()).decode()
    except Exception:
        return ""


# ══════════════════════════════════════════════════════════════════════════════
# LOGIN PAGE — shown when not authenticated
# ══════════════════════════════════════════════════════════════════════════════
if not st.session_state.get("authenticated"):

    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"] { background: #050d1a !important; }
        section[data-testid="stSidebar"]   { display: none !important; }
        [data-testid="collapsedControl"]   { display: none !important; }
        .main .block-container {
            max-width: 460px !important;
            padding: 5rem 1.5rem 2rem !important;
            margin: 0 auto !important;
        }
        .login-shield { font-size: 3rem; text-align: center; margin-bottom: 0.2rem; }
        .login-title {
            font-size: 2.6rem;
            font-weight: 900;
            text-align: center;
            background: linear-gradient(135deg, #00d4ff 0%, #ffffff 50%, #00d4ff 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            filter: drop-shadow(0 0 18px rgba(0,212,255,0.5));
            letter-spacing: 0.42em;
            margin: 0;
        }
        .login-sub {
            text-align: center;
            color: #2d5a6a;
            font-size: 0.68rem;
            letter-spacing: 0.22em;
            text-transform: uppercase;
            margin-top: 0.35rem;
        }
        .login-line {
            width: 160px;
            height: 1px;
            background: linear-gradient(90deg, transparent, #00d4ff, transparent);
            margin: 1.3rem auto 2rem;
        }
        .login-footer {
            text-align: center;
            color: #1e3a45;
            font-size: 0.7rem;
            margin-top: 2rem;
            letter-spacing: 0.08em;
        }
        /* Style the form container */
        [data-testid="stForm"] {
            background: rgba(0,15,30,0.85) !important;
            border: 1px solid rgba(0,212,255,0.15) !important;
            border-radius: 14px !important;
            padding: 1.6rem 1.8rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="login-shield">🛡</div>
        <div class="login-title">SENTINEL</div>
        <div class="login-sub">Security Operations · Restricted Access</div>
        <div class="login-line"></div>
        """,
        unsafe_allow_html=True,
    )

    config = _load_config()

    tab_login, tab_register = st.tabs(["Log In", "Create Account"])

    # ── Log In ────────────────────────────────────────────────────────────────
    with tab_login:
        with st.form("login_form", clear_on_submit=False):
            username_input = st.text_input("Username", placeholder="Enter your username")
            password_input = st.text_input("Password", type="password", placeholder="Enter your password")
            submitted = st.form_submit_button("Log In", use_container_width=True, type="primary")

        if submitted:
            if _check_password(username_input, password_input, config):
                info = _user_info(username_input, config)
                st.session_state["authenticated"] = True
                st.session_state["username"]      = username_input.strip().lower()
                st.session_state["display_name"]  = info.get("name", username_input)
                st.session_state["role"]          = info.get("role", "viewer")
                st.rerun()
            else:
                st.error("Incorrect username or password — check caps lock and try again.")

    # ── Create Account ────────────────────────────────────────────────────────
    with tab_register:
        with st.form("register_form", clear_on_submit=True):
            reg_display  = st.text_input("Full Name", placeholder="Your name")
            reg_username = st.text_input("Username", placeholder="lowercase, no spaces")
            reg_email    = st.text_input("Email (optional)", placeholder="you@example.com")
            reg_pw       = st.text_input("Password", type="password", placeholder="At least 8 characters")
            reg_pw2      = st.text_input("Confirm Password", type="password", placeholder="Repeat your password")
            reg_btn      = st.form_submit_button("Create Account", use_container_width=True, type="primary")

        if reg_btn:
            un  = reg_username.strip().lower()
            err = None
            if not reg_display.strip():
                err = "Full name is required."
            elif not un:
                err = "Username is required."
            elif not un.replace("_", "").replace("-", "").isalnum():
                err = "Username can only contain letters, numbers, hyphens, and underscores."
            elif un in config["credentials"]["usernames"]:
                err = f"Username '{un}' is already taken — choose another."
            elif len(reg_pw) < 8:
                err = "Password must be at least 8 characters."
            elif reg_pw != reg_pw2:
                err = "Passwords do not match."

            if err:
                st.error(err)
            else:
                pw_hash = bcrypt.hashpw(reg_pw.encode(), bcrypt.gensalt(12)).decode()
                config["credentials"]["usernames"][un] = {
                    "name":     reg_display.strip(),
                    "email":    reg_email.strip(),
                    "password": pw_hash,
                    "role":     "viewer",
                }
                _save_config(config)
                st.session_state["authenticated"] = True
                st.session_state["username"]      = un
                st.session_state["display_name"]  = reg_display.strip()
                st.session_state["role"]          = "viewer"
                st.rerun()

    st.markdown(
        '<div class="login-footer">Sentinel v1.0 · Jeremiah Harden · Kennesaw State University</div>',
        unsafe_allow_html=True,
    )

    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
# AUTHENTICATED — full app
# ══════════════════════════════════════════════════════════════════════════════
_photo = _img_b64("jeremiah.png")
_role  = st.session_state.get("role", "viewer")
_uname = st.session_state.get("display_name", "")

with st.sidebar:
    st.markdown(
        """
        <div style="text-align:center;padding:1rem 0 0.5rem;">
            <span style="font-size:2rem;">🛡</span><br>
            <span style="color:#00d4ff;font-size:1.2rem;font-weight:900;letter-spacing:0.2em;">SENTINEL</span><br>
            <span style="color:#0a5a70;font-size:0.72rem;letter-spacing:0.12em;">SECURITY OPERATIONS</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()

    if _photo:
        st.markdown(
            f"""
            <div style="text-align:center;padding:0.5rem 0 0.2rem;">
                <div style="font-size:0.65rem;font-weight:700;letter-spacing:0.18em;
                            text-transform:uppercase;color:#888888;margin-bottom:0.55rem;">
                    Founder
                </div>
                <img src="{_photo}"
                     style="width:110px;height:110px;border-radius:50%;
                            object-fit:cover;object-position:center top;
                            border:2px solid #444444;
                            box-shadow:0 0 14px rgba(255,255,255,0.08);">
            </div>
            <div style="text-align:center;padding:0.75rem 0.5rem 0.25rem;color:#ffffff;">
                <div style="font-size:0.95rem;font-weight:700;letter-spacing:0.04em;">
                    Jeremiah Harden
                </div>
                <div style="font-size:0.72rem;color:#888888;margin-top:0.2rem;letter-spacing:0.06em;text-transform:uppercase;">
                    Cybersecurity · Kennesaw State University
                </div>
                <a href="https://www.linkedin.com/in/jeremiah-harden-50ba4331a/"
                   target="_blank"
                   style="display:inline-flex;align-items:center;gap:0.35rem;
                          margin-top:0.55rem;padding:0.3rem 0.85rem;
                          background:#0a66c2;border-radius:20px;
                          font-size:0.72rem;font-weight:600;color:#ffffff;
                          text-decoration:none;letter-spacing:0.04em;">
                    in&nbsp; LinkedIn
                </a>
            </div>
            <div style="font-size:0.78rem;color:#aaaaaa;line-height:1.6;
                        padding:0.6rem 0.75rem 0.5rem;text-align:center;
                        border-top:1px solid #222222;border-bottom:1px solid #222222;
                        margin:0.4rem 0 0.6rem;">
                Hello, my name is Jeremiah Harden. I build security tools
                to put what I study into practice. Sentinel parses raw logs,
                detects active threats, and maps attack origins the same way
                a SOC analyst would. This is not just a project. This is how I prepare.
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()

    # Logged-in user badge
    st.markdown(
        f"""
        <div style="background:rgba(0,212,255,0.07);border:1px solid rgba(0,212,255,0.18);
                    border-radius:10px;padding:0.55rem 0.8rem;margin-bottom:0.4rem;">
            <div style="font-size:0.62rem;font-weight:700;letter-spacing:0.16em;
                        color:#00d4ff;text-transform:uppercase;margin-bottom:0.2rem;">
                Logged in as
            </div>
            <div style="color:#ffffff;font-size:0.88rem;font-weight:600;">{_uname}</div>
            <div style="font-size:0.65rem;color:#3a7a8a;text-transform:uppercase;
                        letter-spacing:0.1em;margin-top:0.1rem;">{_role}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Log Out", use_container_width=True):
        for key in ["authenticated", "username", "display_name", "role"]:
            st.session_state.pop(key, None)
        st.rerun()

    st.divider()

# ── Navigation (role-aware) ───────────────────────────────────────────────────
pages = [
    st.Page("pages/welcome.py",   title="Home",      icon="🏠", default=True),
    st.Page("pages/dashboard.py", title="Dashboard", icon="📊"),
    st.Page("pages/tools.py",     title="Tools",     icon="⚡"),
]

if _role == "admin":
    pages.append(st.Page("pages/admin.py", title="Users", icon="👥"))

pg = st.navigation(pages, position="sidebar")
pg.run()
