"""
Persistent config storage via GitHub Gist + stateless HMAC session cookies.

Add to Streamlit Cloud secrets:
    GITHUB_TOKEN  = "ghp_..."   # PAT with 'gist' scope ONLY (not repo — no redeploys triggered)
    COOKIE_SECRET = "any-random-string"
    GIST_ID       = "..."       # optional — auto-created on first run, saved to auth/.gist_id

Falls back to local config.yaml when no token is configured (local dev works unchanged).
"""
import base64
import hashlib
import hmac
import json
import time
from pathlib import Path

import requests
import yaml

_CFG_PATH     = Path(__file__).parent / "config.yaml"
_GIST_ID_FILE = Path(__file__).parent / ".gist_id"  # written on first Gist creation

# Simple in-process cache so we don't hit the GitHub API on every page render.
# Streamlit reruns the whole script on every interaction, so without this
# every button click would make a network request.
_CACHE: dict = {"data": None, "ts": 0.0}
_CACHE_TTL   = 30   # re-read Gist at most every 30 s
_TOKEN_TTL   = 7 * 24 * 3600  # cookie lifetime: 7 days


# ── Secrets ────────────────────────────────────────────────────────────────────
# These are read lazily (inside functions, not at import time) so that Streamlit's
# context is fully initialized before we access st.secrets. Importing this module
# from a script that doesn't use Streamlit won't crash.

def _get_token() -> str:
    try:
        import streamlit as st
        return st.secrets.get("GITHUB_TOKEN", "")
    except Exception:
        return ""


def _get_cookie_secret() -> str:
    try:
        import streamlit as st
        v = st.secrets.get("COOKIE_SECRET", "")
        return v if v else "sentinel-fallback-insecure"
    except Exception:
        return "sentinel-fallback-insecure"


def _get_gist_id() -> str:
    try:
        import streamlit as st
        v = st.secrets.get("GIST_ID", "")
        if v:
            return v
    except Exception:
        pass
    try:
        return _GIST_ID_FILE.read_text().strip()
    except Exception:
        return ""


def _headers(token: str) -> dict:
    return {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}


# ── Gist helpers ───────────────────────────────────────────────────────────────

def _create_gist(token: str) -> str:
    content = _CFG_PATH.read_text(encoding="utf-8")
    r = requests.post(
        "https://api.github.com/gists",
        headers=_headers(token),
        json={
            "description": "Sentinel user config — managed by app",
            "public": False,
            "files": {"config.yaml": {"content": content}},
        },
        timeout=10,
    )
    r.raise_for_status()
    gist_id = r.json()["id"]
    try:
        _GIST_ID_FILE.write_text(gist_id)
    except Exception:
        pass
    return gist_id


# ── Public API ─────────────────────────────────────────────────────────────────

def load_config() -> dict:
    token   = _get_token()
    gist_id = _get_gist_id()

    if token:
        if not gist_id:
            try:
                gist_id = _create_gist(token)
            except Exception:
                pass

        if gist_id:
            now = time.time()
            if _CACHE["data"] and (now - _CACHE["ts"]) < _CACHE_TTL:
                return _CACHE["data"]
            try:
                r = requests.get(
                    f"https://api.github.com/gists/{gist_id}",
                    headers=_headers(token),
                    timeout=5,
                )
                r.raise_for_status()
                raw  = r.json()["files"]["config.yaml"]["content"]
                data = yaml.safe_load(raw)
                _CACHE["data"] = data
                _CACHE["ts"]   = now
                return data
            except Exception:
                pass

    with open(_CFG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_config(cfg: dict) -> None:
    with open(_CFG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True)

    _CACHE["data"] = None

    token   = _get_token()
    gist_id = _get_gist_id()
    if token and gist_id:
        try:
            content = yaml.dump(cfg, default_flow_style=False, allow_unicode=True)
            requests.patch(
                f"https://api.github.com/gists/{gist_id}",
                headers=_headers(token),
                json={"files": {"config.yaml": {"content": content}}},
                timeout=10,
            )
        except Exception:
            pass


# ── Stateless HMAC session cookies ─────────────────────────────────────────────

def make_session_cookie(username: str, display_name: str, role: str) -> str:
    """Create a stateless, tamper-proof session cookie value.

    Structure: base64url(json_payload) + "." + HMAC-SHA256(base64url(payload), secret)

    Why stateless (no server-side file)?
      tokens.json lived on Streamlit Cloud's ephemeral filesystem and was wiped
      on every redeploy. A self-contained signed cookie survives redeploys,
      server restarts, and even multi-instance deployments — the secret is the
      only thing that needs to be consistent, and it lives in Streamlit secrets.

    Why HMAC instead of just base64?
      Base64 is reversible by anyone. HMAC signs the payload with a secret key
      so an attacker can't forge a cookie claiming to be 'admin' — they'd need
      the secret to produce a valid signature.

    The payload is JSON with short keys (u/n/r/e) to keep cookie size small.
    """
    secret  = _get_cookie_secret()
    expires = int(time.time()) + _TOKEN_TTL
    payload = json.dumps(
        {"u": username, "n": display_name, "r": role, "e": expires},
        separators=(",", ":"),   # compact JSON — no spaces
    )
    b64 = base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")
    sig = hmac.new(secret.encode(), b64.encode(), hashlib.sha256).hexdigest()
    return f"{b64}.{sig}"


def read_session_cookie(value: str) -> dict | None:
    """Validate a session cookie and return the session data, or None if invalid.

    Validation steps:
      1. Split on the last "." to get (payload_b64, signature).
      2. Recompute the expected HMAC with our secret.
      3. Compare with hmac.compare_digest — constant-time comparison prevents
         timing attacks where an attacker probes one character at a time.
      4. Decode the base64 payload and check the expiry timestamp.

    Returns None (not an exception) on any failure so callers can safely do
    `if read_session_cookie(value):` without a try/except.
    """
    if not value:
        return None
    try:
        secret   = _get_cookie_secret()
        b64, sig = value.rsplit(".", 1)
        expected = hmac.new(secret.encode(), b64.encode(), hashlib.sha256).hexdigest()
        # Constant-time comparison — prevents timing-based signature oracle attacks
        if not hmac.compare_digest(sig, expected):
            return None
        # Add back the base64 padding that make_session_cookie stripped
        padding = (4 - len(b64) % 4) % 4
        data    = json.loads(base64.urlsafe_b64decode(b64 + "=" * padding))
        if data["e"] < time.time():
            return None   # cookie is valid but expired
        return {"username": data["u"], "display_name": data["n"], "role": data["r"]}
    except Exception:
        return None
