import base64
import hmac
import json
import random
import time
import uuid
from pathlib import Path

import bcrypt
import streamlit as st
import yaml

try:
    from streamlit_cookies_controller import CookieController
    _COOKIES_AVAILABLE = True
except Exception:
    _COOKIES_AVAILABLE = False

st.set_page_config(
    page_title="Sentinel",
    page_icon="🛡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Paths ──────────────────────────────────────────────────────────────────────
_CFG_PATH   = Path(__file__).parent / "auth" / "config.yaml"
_SESS_PATH  = Path(__file__).parent / "auth" / "sessions.json"
_TOKEN_PATH = Path(__file__).parent / "auth" / "tokens.json"
_TOKEN_TTL  = 7 * 24 * 3600  # 7 days


# ── Config helpers ─────────────────────────────────────────────────────────────
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


# ── Persistent session tokens ──────────────────────────────────────────────────
def _load_tokens() -> dict:
    try:
        if _TOKEN_PATH.exists():
            return json.loads(_TOKEN_PATH.read_text())
    except Exception:
        pass
    return {}


def _save_tokens(tokens: dict) -> None:
    try:
        _TOKEN_PATH.write_text(json.dumps(tokens))
    except Exception:
        pass


def _create_token(username: str, display_name: str, role: str) -> str:
    token = str(uuid.uuid4())
    now   = time.time()
    tokens = _load_tokens()
    tokens = {k: v for k, v in tokens.items() if v.get("expires", 0) > now}
    tokens[token] = {
        "username":     username,
        "display_name": display_name,
        "role":         role,
        "expires":      now + _TOKEN_TTL,
    }
    _save_tokens(tokens)
    return token


def _validate_token(token: str) -> dict | None:
    if not token:
        return None
    tokens = _load_tokens()
    entry  = tokens.get(str(token))
    if not entry:
        return None
    if entry.get("expires", 0) < time.time():
        tokens.pop(str(token), None)
        _save_tokens(tokens)
        return None
    return entry


def _revoke_token(token: str) -> None:
    if not token:
        return
    tokens = _load_tokens()
    tokens.pop(str(token), None)
    _save_tokens(tokens)


# ── Session ping (powers "Online Now" in admin) ────────────────────────────────
def _ping_session(username: str) -> None:
    if not username:
        return
    try:
        data = json.loads(_SESS_PATH.read_text()) if _SESS_PATH.exists() else {}
        data[username] = time.time()
        _SESS_PATH.write_text(json.dumps(data))
    except Exception:
        pass


# ── Image helper ───────────────────────────────────────────────────────────────
def _img_b64(name: str) -> str:
    p = Path(__file__).parent / "assets" / name
    try:
        ext = p.suffix.lstrip(".")
        return f"data:image/{ext};base64," + base64.b64encode(p.read_bytes()).decode()
    except Exception:
        return ""


def _new_captcha(prefix: str = "captcha_") -> None:
    st.session_state[f"{prefix}a"] = random.randint(2, 15)
    st.session_state[f"{prefix}b"] = random.randint(2, 15)


# ── Cookie controller — gracefully skipped if package unavailable ──────────────
_ctrl = None
if _COOKIES_AVAILABLE:
    try:
        _ctrl = CookieController()
    except Exception:
        pass

# ── Restore session from persistent cookie on page refresh ─────────────────────
if not st.session_state.get("authenticated") and _ctrl is not None:
    try:
        _saved_token = _ctrl.get("sentinel_session")
        if _saved_token:
            _session_data = _validate_token(_saved_token)
            if _session_data:
                st.session_state["authenticated"]  = True
                st.session_state["username"]       = _session_data["username"]
                st.session_state["display_name"]   = _session_data["display_name"]
                st.session_state["role"]           = _session_data["role"]
                st.session_state["session_token"]  = _saved_token
                st.rerun()
    except Exception:
        pass


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
            max-width: 480px !important;
            padding: 4rem 1.5rem 2rem !important;
            margin: 0 auto !important;
        }
        .login-shield { font-size: 3rem; text-align: center; margin-bottom: 0.2rem; }
        .login-title {
            font-size: 2.6rem; font-weight: 900; text-align: center;
            background: linear-gradient(135deg, #00d4ff 0%, #ffffff 50%, #00d4ff 100%);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            background-clip: text;
            filter: drop-shadow(0 0 18px rgba(0,212,255,0.5));
            letter-spacing: 0.42em; margin: 0;
        }
        .login-sub {
            text-align: center; color: #2d5a6a; font-size: 0.68rem;
            letter-spacing: 0.22em; text-transform: uppercase; margin-top: 0.35rem;
        }
        .login-line {
            width: 160px; height: 1px;
            background: linear-gradient(90deg, transparent, #00d4ff, transparent);
            margin: 1.3rem auto 1.8rem;
        }
        .login-footer {
            text-align: center; color: #1e3a45; font-size: 0.7rem;
            margin-top: 2rem; letter-spacing: 0.08em;
        }
        [data-testid="stForm"] {
            background: rgba(0,15,30,0.85) !important;
            border: 1px solid rgba(0,212,255,0.15) !important;
            border-radius: 14px !important; padding: 1.6rem 1.8rem !important;
        }
        .login-features {
            background: rgba(0,212,255,0.04);
            border: 1px solid rgba(0,212,255,0.12);
            border-radius: 10px; padding: 0.8rem 1rem; margin-bottom: 1.4rem;
        }
        .feat-row {
            display: flex; align-items: flex-start; gap: 0.6rem;
            padding: 0.28rem 0; border-bottom: 1px solid rgba(0,212,255,0.05);
        }
        .feat-row:last-child { border-bottom: none; }
        .feat-icon { font-size: 0.9rem; flex-shrink: 0; padding-top: 0.05rem; }
        .feat-text { color: #5a8fa0; font-size: 0.76rem; line-height: 1.45; }
        .feat-text strong { color: #00d4ff; font-weight: 700; }
        .captcha-box {
            background: rgba(0,212,255,0.03);
            border: 1px solid rgba(0,212,255,0.22);
            border-radius: 8px; padding: 0.65rem 1rem 0.5rem;
            margin-bottom: 0.5rem; text-align: center;
        }
        .captcha-label {
            font-size: 0.6rem; font-weight: 700; letter-spacing: 0.18em;
            color: #00d4ff; text-transform: uppercase; margin-bottom: 0.2rem;
        }
        .captcha-problem {
            font-size: 1.55rem; font-weight: 900; color: #ffffff;
            font-family: 'Courier New', monospace; letter-spacing: 0.1em;
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

    st.markdown(
        """
        <div class="login-features">
            <div class="feat-row">
                <span class="feat-icon">⚡</span>
                <span class="feat-text"><strong>Free cyber tools</strong> — hash generator, base64 encoder, password analyzer &amp; generator, IP lookup, Caesar cipher</span>
            </div>
            <div class="feat-row">
                <span class="feat-icon">🔍</span>
                <span class="feat-text"><strong>Log analysis engine</strong> — upload any log file to detect SSH brute force, SQL injection, XSS, and directory scans</span>
            </div>
            <div class="feat-row">
                <span class="feat-icon">🌍</span>
                <span class="feat-text"><strong>Attack origin mapping</strong> — geolocate attacker IPs on a live world map with severity scoring</span>
            </div>
            <div class="feat-row">
                <span class="feat-icon">🛡</span>
                <span class="feat-text"><strong>SOC-grade threat detection</strong> — incident reports with severity scoring, timelines, and downloadable HTML reports</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "captcha_a" not in st.session_state:
        _new_captcha("captcha_")
    if "captcha_reg_a" not in st.session_state:
        _new_captcha("captcha_reg_")

    config = _load_config()
    tab_login, tab_register = st.tabs(["Log In", "Create Account"])

    # ── Log In ────────────────────────────────────────────────────────────────
    with tab_login:
        _ca = st.session_state["captcha_a"]
        _cb = st.session_state["captcha_b"]
        with st.form("login_form", clear_on_submit=False):
            username_input = st.text_input("Username", placeholder="Enter your username")
            password_input = st.text_input("Password", type="password", placeholder="Enter your password")
            st.markdown(
                f'<div class="captcha-box">'
                f'<div class="captcha-label">🤖 Human Verification — solve to continue</div>'
                f'<div class="captcha-problem">{_ca} + {_cb} = ?</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            captcha_login = st.text_input("Answer", placeholder="Type the number", key="cap_login")
            submitted = st.form_submit_button("Log In", use_container_width=True, type="primary")

        if submitted:
            try:
                cap_ok = int(captcha_login.strip()) == _ca + _cb
            except (ValueError, TypeError):
                cap_ok = False

            if not cap_ok:
                _new_captcha("captcha_")
                st.error("Human verification failed — a new equation has been generated, try again.")
            elif _check_password(username_input, password_input, config):
                info    = _user_info(username_input, config)
                un      = username_input.strip().lower()
                dname   = info.get("name", username_input)
                role    = info.get("role", "viewer")
                token   = _create_token(un, dname, role)
                st.session_state["authenticated"]  = True
                st.session_state["username"]       = un
                st.session_state["display_name"]   = dname
                st.session_state["role"]           = role
                st.session_state["session_token"]  = token
                if _ctrl is not None:
                    try:
                        _ctrl.set("sentinel_session", token)
                    except Exception:
                        pass
                st.rerun()
            else:
                _new_captcha("captcha_")
                st.error("Incorrect username or password — check caps lock and try again.")

    # ── Create Account ────────────────────────────────────────────────────────
    with tab_register:
        _ra = st.session_state["captcha_reg_a"]
        _rb = st.session_state["captcha_reg_b"]
        with st.form("register_form", clear_on_submit=True):
            reg_display  = st.text_input("Full Name",        placeholder="Your name")
            reg_username = st.text_input("Username",         placeholder="lowercase, no spaces")
            reg_email    = st.text_input("Email (optional)", placeholder="you@example.com")
            reg_pw       = st.text_input("Password",         type="password", placeholder="At least 8 characters")
            reg_pw2      = st.text_input("Confirm Password", type="password", placeholder="Repeat your password")
            st.markdown(
                f'<div class="captcha-box">'
                f'<div class="captcha-label">🤖 Human Verification — solve to continue</div>'
                f'<div class="captcha-problem">{_ra} + {_rb} = ?</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            captcha_reg = st.text_input("Answer", placeholder="Type the number", key="cap_reg")
            reg_btn     = st.form_submit_button("Create Account", use_container_width=True, type="primary")

        if reg_btn:
            try:
                reg_cap_ok = int(captcha_reg.strip()) == _ra + _rb
            except (ValueError, TypeError):
                reg_cap_ok = False

            if not reg_cap_ok:
                _new_captcha("captcha_reg_")
                st.error("Human verification failed — a new equation has been generated, try again.")
            else:
                un  = reg_username.strip().lower()
                err = None
                if not reg_display.strip():
                    err = "Full name is required."
                elif not un:
                    err = "Username is required."
                elif not un.replace("_", "").replace("-", "").isalnum():
                    err = "Username may only contain letters, numbers, hyphens, and underscores."
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
                    dname  = reg_display.strip()
                    token  = _create_token(un, dname, "viewer")
                    st.session_state["authenticated"]  = True
                    st.session_state["username"]       = un
                    st.session_state["display_name"]   = dname
                    st.session_state["role"]           = "viewer"
                    st.session_state["session_token"]  = token
                    if _ctrl is not None:
                        try:
                            _ctrl.set("sentinel_session", token)
                        except Exception:
                            pass
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
_ping_session(st.session_state.get("username", ""))

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
        _revoke_token(st.session_state.get("session_token", ""))
        if _ctrl is not None:
            try:
                _ctrl.remove("sentinel_session")
            except Exception:
                pass
        for key in [
            "authenticated", "username", "display_name", "role", "session_token",
            "captcha_a", "captcha_b", "captcha_reg_a", "captcha_reg_b",
            "admin_reauth_time",
        ]:
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
    pages.append(st.Page("pages/admin.py", title="Admin", icon="⚙"))

pg = st.navigation(pages, position="sidebar")
pg.run()
