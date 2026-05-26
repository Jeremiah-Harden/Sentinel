import hashlib
import base64 as b64_module
import ipaddress
import re
import secrets
import string

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

st.markdown(
    """
    <style>
    [data-testid="stAppViewContainer"] {
        background: #050d1a !important;
    }
    [data-testid="stSidebar"]        { background: #0d0d0d !important; }
    [data-testid="stSidebarContent"] { background: #0d0d0d !important; }

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
    .page-sub {
        color: #4d7a8a;
        font-size: 0.88rem;
        letter-spacing: 0.05em;
        margin-bottom: 1.5rem;
    }
    .result-box {
        background: rgba(0,212,255,0.05);
        border: 1px solid rgba(0,212,255,0.18);
        border-radius: 10px;
        padding: 0.85rem 1.1rem;
        margin: 0.4rem 0;
        font-family: monospace;
        font-size: 0.87rem;
        color: #00d4ff;
        word-break: break-all;
        line-height: 1.5;
    }
    .result-label {
        color: #4d7a8a;
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        margin-bottom: 0.15rem;
        margin-top: 0.6rem;
    }
    .strength-val {
        font-size: 1.15rem;
        font-weight: 800;
        letter-spacing: 0.05em;
        margin-bottom: 0.25rem;
    }
    .tip-row {
        display: flex;
        align-items: flex-start;
        gap: 0.5rem;
        font-size: 0.83rem;
        color: #7799aa;
        padding: 0.22rem 0;
    }
    .stTabs [data-baseweb="tab"] {
        font-weight: 600;
        letter-spacing: 0.04em;
    }
    .block-container { padding-top: 2rem !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="page-header">⚡ Cyber Tools</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="page-sub">Quick-access security utilities — everything runs locally, no data leaves your machine</div>',
    unsafe_allow_html=True,
)

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["🔐 Hash Generator", "📦 Base64", "🔑 Password Strength", "🌍 IP Lookup", "🔄 Caesar Cipher"]
)

# ── Hash Generator ────────────────────────────────────────────────────────────
with tab1:
    st.markdown("#### Hash Generator")
    st.caption("Compute cryptographic hashes of any text. Useful for verifying file integrity, storing passwords, and CTF challenges.")

    h_input = st.text_area("Input text", height=130, placeholder="Type or paste text here…", key="h_input")

    algo_cols = st.columns(5)
    selected = {}
    for col, algo in zip(algo_cols, ["MD5", "SHA-1", "SHA-256", "SHA-512", "SHA3-256"]):
        selected[algo] = col.checkbox(algo, value=True, key=f"ck_{algo}")

    if h_input:
        raw = h_input.encode("utf-8")
        digests = {
            "MD5":      hashlib.md5(raw).hexdigest(),
            "SHA-1":    hashlib.sha1(raw).hexdigest(),
            "SHA-256":  hashlib.sha256(raw).hexdigest(),
            "SHA-512":  hashlib.sha512(raw).hexdigest(),
            "SHA3-256": hashlib.sha3_256(raw).hexdigest(),
        }
        for algo, digest in digests.items():
            if selected.get(algo):
                st.markdown(f'<div class="result-label">{algo}</div><div class="result-box">{digest}</div>', unsafe_allow_html=True)
    else:
        st.info("Enter text above to generate hashes.")

# ── Base64 ────────────────────────────────────────────────────────────────────
with tab2:
    st.markdown("#### Base64 Encoder / Decoder")
    st.caption("Encode text or binary data to Base64, or decode Base64 strings back to plaintext. Common in web tokens, email, and obfuscated payloads.")

    b64_mode = st.radio("Mode", ["Encode", "Decode"], horizontal=True, key="b64_mode")
    b64_in = st.text_area(
        "Input",
        height=140,
        placeholder="Enter text to encode…" if b64_mode == "Encode" else "Enter Base64 string to decode…",
        key="b64_in",
    )

    if b64_in.strip():
        try:
            if b64_mode == "Encode":
                out = b64_module.b64encode(b64_in.encode("utf-8")).decode("ascii")
                lbl = "Encoded (Base64)"
            else:
                out = b64_module.b64decode(b64_in.strip()).decode("utf-8", errors="replace")
                lbl = "Decoded (plaintext)"
            st.markdown(f'<div class="result-label">{lbl}</div><div class="result-box">{out}</div>', unsafe_allow_html=True)
            st.code(out, language=None)
        except Exception as exc:
            st.error(f"Error: {exc}")
    else:
        st.info("Enter text above to encode or decode.")

# ── Password Strength ─────────────────────────────────────────────────────────
with tab3:
    st.markdown("#### Password Strength Analyzer")
    st.caption("Checks your password against eight security criteria and gives you actionable feedback.")

    pw = st.text_input("Password", type="password", placeholder="Enter a password to analyze…", key="pw")

    if pw:
        checks = [
            (len(pw) >= 12,
             "12 or more characters"),
            (len(pw) >= 16,
             "16 or more characters (extra credit)"),
            (bool(re.search(r"[A-Z]", pw)),
             "Contains uppercase letters"),
            (bool(re.search(r"[a-z]", pw)),
             "Contains lowercase letters"),
            (bool(re.search(r"\d", pw)),
             "Contains numbers"),
            (bool(re.search(r"""[!@#$%^&*()\[\]{};:',.<>?/\\|`~\-_=+]""", pw)),
             "Contains special characters"),
            (not bool(re.search(r"(.)\1{2,}", pw)),
             "No repeated character runs (aaa, 111…)"),
            (not any(s in pw.lower() for s in ["password", "123456", "qwerty", "admin", "letmein", "welcome"]),
             "No obvious common patterns"),
        ]

        passed  = [lbl for ok, lbl in checks if ok]
        failed  = [lbl for ok, lbl in checks if not ok]
        score   = len(passed)
        display = min(5, round(score * 5 / len(checks)))

        color_map = {0: "#ef4444", 1: "#ef4444", 2: "#f97316", 3: "#f59e0b", 4: "#4ade80", 5: "#00d4ff"}
        label_map = {0: "Very Weak", 1: "Weak", 2: "Fair", 3: "Good", 4: "Strong", 5: "Very Strong"}

        st.markdown(
            f'<div class="strength-val" style="color:{color_map[display]};">{label_map[display]}</div>',
            unsafe_allow_html=True,
        )
        st.progress(display / 5)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Passed**")
            for lbl in passed:
                st.markdown(f'<div class="tip-row">✅ {lbl}</div>', unsafe_allow_html=True)
        with c2:
            st.markdown("**Needs work**")
            if failed:
                for lbl in failed:
                    st.markdown(f'<div class="tip-row">⚠️ {lbl}</div>', unsafe_allow_html=True)
            else:
                st.success("All criteria met!")
    else:
        st.info("Enter a password above to analyze its strength.")

    st.divider()
    st.markdown("#### Password Generator")
    st.caption("Generate a cryptographically secure random password, then paste it into the field above to check its strength.")

    g_len = st.slider("Length", min_value=8, max_value=64, value=16, key="g_len")
    g1, g2, g3, g4 = st.columns(4)
    g_upper  = g1.checkbox("A-Z uppercase",  value=True, key="g_upper")
    g_lower  = g2.checkbox("a-z lowercase",  value=True, key="g_lower")
    g_digits = g3.checkbox("0-9 digits",     value=True, key="g_digits")
    g_spec   = g4.checkbox("!@# symbols",    value=True, key="g_spec")

    SYMBOLS = "!@#$%^&*()-_=+[]{}|;:,.<>?"

    if st.button("Generate", type="primary", key="gen_btn"):
        pool = ""
        required = []
        if g_upper:  pool += string.ascii_uppercase;  required.append(secrets.choice(string.ascii_uppercase))
        if g_lower:  pool += string.ascii_lowercase;  required.append(secrets.choice(string.ascii_lowercase))
        if g_digits: pool += string.digits;           required.append(secrets.choice(string.digits))
        if g_spec:   pool += SYMBOLS;                 required.append(secrets.choice(SYMBOLS))

        if not pool:
            st.warning("Select at least one character set.")
        else:
            padding = [secrets.choice(pool) for _ in range(g_len - len(required))]
            combined = required + padding
            secrets.SystemRandom().shuffle(combined)
            st.session_state["gen_pw"] = "".join(combined)

    if "gen_pw" in st.session_state:
        st.markdown(
            f'<div class="result-label">Generated Password</div>'
            f'<div class="result-box">{st.session_state["gen_pw"]}</div>',
            unsafe_allow_html=True,
        )
        st.code(st.session_state["gen_pw"], language=None)
        st.caption("Copy the password above into the input field to run the strength check on it.")

# ── IP Lookup ─────────────────────────────────────────────────────────────────
with tab4:
    st.markdown("#### IP Geolocation Lookup")
    st.caption("Resolve any public IP to its country, city, ISP, and coordinates using ip-api.com — free, no API key needed.")

    ip_raw = st.text_input("IP Address", placeholder="e.g. 8.8.8.8 or 185.220.101.1", key="ip_raw")

    if ip_raw.strip():
        if st.button("Look Up", key="ip_btn"):
            ip_str = ip_raw.strip()
            try:
                addr = ipaddress.ip_address(ip_str)
                if addr.is_private or addr.is_loopback:
                    st.warning("Private or loopback IPs cannot be geolocated — enter a public IP.")
                else:
                    with st.spinner("Looking up…"):
                        resp = requests.get(
                            f"http://ip-api.com/json/{ip_str}",
                            params={"fields": "status,message,country,regionName,city,zip,lat,lon,isp,org,as,query"},
                            timeout=6,
                        )
                    data = resp.json()
                    if data.get("status") == "success":
                        r1, r2 = st.columns(2)
                        r1.metric("Country", data.get("country", "—"))
                        r2.metric("City",    data.get("city", "—"))
                        r1.metric("Region",  data.get("regionName", "—"))
                        r2.metric("ZIP",     data.get("zip", "—"))
                        st.metric("ISP", data.get("isp", "—"))
                        st.metric("Org", data.get("org", "—"))
                        st.metric("AS",  data.get("as", "—"))

                        lat, lon = data.get("lat"), data.get("lon")
                        if lat and lon:
                            df_pt = pd.DataFrame([{"lat": lat, "lon": lon, "ip": ip_str}])
                            fig = px.scatter_geo(
                                df_pt, lat="lat", lon="lon",
                                hover_data={"ip": True, "lat": False, "lon": False},
                                projection="natural earth",
                            )
                            fig.update_traces(marker=dict(size=16, color="#00d4ff", symbol="circle"))
                            fig.update_layout(
                                geo=dict(
                                    bgcolor="#050d1a", showland=True, landcolor="#0a1628",
                                    showocean=True, oceancolor="#050d1a",
                                    showcountries=True, countrycolor="#1a3050",
                                ),
                                plot_bgcolor="#050d1a", paper_bgcolor="#050d1a",
                                font_color="#d0e8f8",
                                margin=dict(l=0, r=0, t=10, b=0),
                                height=320,
                            )
                            st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.error(f"Lookup failed: {data.get('message', 'unknown error')}")
            except ValueError:
                st.error("Not a valid IP address format.")
            except Exception as exc:
                st.error(f"Request failed: {exc}")
    else:
        st.info("Enter an IP address above and click Look Up.")

# ── Caesar Cipher ─────────────────────────────────────────────────────────────
with tab5:
    st.markdown("#### Caesar Cipher / ROT13")
    st.caption("Shifts every letter by a fixed amount. ROT13 (shift 13) is commonly used to obscure spoilers and CTF hints. Shift 3 is the classic Caesar cipher.")

    c_mode  = st.radio("Mode", ["Encode", "Decode"], horizontal=True, key="c_mode")
    c_text  = st.text_area("Input text", height=130, placeholder="Enter text to encode or decode…", key="c_text")
    c_shift = st.slider("Shift amount (ROT13 = 13, classic Caesar = 3)", 1, 25, 13, key="c_shift")

    if c_text.strip():
        shift = c_shift if c_mode == "Encode" else (26 - c_shift)
        out_chars = []
        for ch in c_text:
            if ch.isalpha():
                base = ord("A") if ch.isupper() else ord("a")
                out_chars.append(chr((ord(ch) - base + shift) % 26 + base))
            else:
                out_chars.append(ch)
        result = "".join(out_chars)
        lbl = f"{'Encoded' if c_mode == 'Encode' else 'Decoded'} (shift {c_shift})"
        st.markdown(f'<div class="result-label">{lbl}</div><div class="result-box">{result}</div>', unsafe_allow_html=True)
        st.code(result, language=None)
    else:
        st.info("Enter text above to apply the cipher.")
