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

    /* ── About / educational section ── */
    .about-wrap {
        background: rgba(0,15,30,0.75);
        border: 1px solid rgba(0,212,255,0.1);
        border-radius: 12px;
        padding: 1.3rem 1.6rem 1.4rem;
        margin-top: 0.4rem;
    }
    .about-h {
        color: #00d4ff;
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.18em;
        text-transform: uppercase;
        border-bottom: 1px solid rgba(0,212,255,0.12);
        padding-bottom: 0.3rem;
        margin-bottom: 0.55rem;
        margin-top: 1.1rem;
    }
    .about-h:first-child { margin-top: 0; }
    .about-p {
        color: #8ab0c4;
        font-size: 0.86rem;
        line-height: 1.72;
        margin: 0;
    }
    .about-ex {
        background: rgba(0,0,0,0.45);
        border-left: 3px solid #00d4ff;
        border-radius: 0 8px 8px 0;
        padding: 0.55rem 1rem;
        font-family: monospace;
        font-size: 0.83rem;
        color: #55ddf0;
        margin: 0.35rem 0;
        line-height: 1.65;
        word-break: break-all;
    }
    .about-li {
        color: #8ab0c4;
        font-size: 0.86rem;
        line-height: 1.65;
        padding: 0.18rem 0;
        padding-left: 1rem;
        position: relative;
    }
    .about-li::before {
        content: "›";
        color: #00d4ff;
        position: absolute;
        left: 0;
        font-weight: 700;
    }
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

    with st.expander("📚 About this tool — examples, student uses, and why companies rely on it"):
        st.markdown(
            """
            <div class="about-wrap">
                <div class="about-h">What cybersecurity students can do with it</div>
                <div class="about-li">CTF competitions frequently hand you a hash and ask you to identify the algorithm or crack a weak one using wordlists with tools like Hashcat or John the Ripper — this tool lets you practice generating and recognizing each format.</div>
                <div class="about-li">Verify that a downloaded file has not been tampered with by computing its hash and comparing it to the vendor's published checksum.</div>
                <div class="about-li">Understand how databases store passwords — they hash them and never keep plaintext, so a breach leaks hashes, not passwords directly.</div>
                <div class="about-li">Practice distinguishing hash types by output length: MD5 = 32 hex characters, SHA-1 = 40, SHA-256 = 64, SHA-512 = 128.</div>

                <div class="about-h">Example</div>
                <div class="about-ex">
                    Input: "password123"<br>
                    MD5:      482c811da5d5b4bc6d497ffa98491e38<br>
                    SHA-256:  ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f<br><br>
                    Change one character — "Password123" — and every hash changes completely (avalanche effect).
                </div>

                <div class="about-h">How it works</div>
                <div class="about-p">A hash function is a one-way mathematical function that converts any input into a fixed-length fingerprint called a digest. The same input always produces the same digest, but even a single character change flips roughly half the output bits. You cannot reverse a hash back to the original input without trying every possible input. MD5 and SHA-1 are now considered broken for security use because collisions have been found. SHA-256 and SHA-512 are the current standards.</div>

                <div class="about-h">Why companies use it</div>
                <div class="about-li">Password storage: every modern authentication system hashes passwords before saving them so a data breach never exposes plaintext credentials.</div>
                <div class="about-li">Software distribution: vendors publish SHA-256 checksums alongside installers so users can verify nothing was modified in transit.</div>
                <div class="about-li">Digital signatures and TLS certificates rely on SHA-256 to bind a public key to an identity.</div>
                <div class="about-li">Blockchain: every Bitcoin block references the hash of the previous block, making the chain tamper-evident without a central authority.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

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

    with st.expander("📚 About this tool — examples, student uses, and why companies rely on it"):
        st.markdown(
            """
            <div class="about-wrap">
                <div class="about-h">What cybersecurity students can do with it</div>
                <div class="about-li">Attackers routinely base64-encode malware commands to bypass text-based security filters and IDS signatures. Decoding these strings is one of the first steps in malware analysis.</div>
                <div class="about-li">Every JWT (JSON Web Token) is three Base64url segments separated by dots. Decode the first two to read the algorithm and the claims without needing any key.</div>
                <div class="about-li">CTF challenges frequently hide flags inside base64 strings buried in HTML source, HTTP headers, or binary blobs.</div>
                <div class="about-li">Email forensics: attachments in MIME messages are base64-encoded and must be decoded before you can inspect or scan them.</div>

                <div class="about-h">Example</div>
                <div class="about-ex">
                    HTTP Basic Auth header value: "YWRtaW46cGFzc3dvcmQ="<br>
                    Decoded → "admin:password"<br><br>
                    Suspicious PowerShell one-liner: powershell -enc UwB0AGEAcgB0AC0AUAByAG8AYwBlAHMAcwA=<br>
                    Decoded → "Start-Process" (classic living-off-the-land technique)
                </div>

                <div class="about-h">How it works</div>
                <div class="about-p">Base64 groups every 3 bytes of binary data into a 24-bit block and splits it into four 6-bit values, each mapped to one of 64 printable ASCII characters (A-Z, a-z, 0-9, + and /). The = padding at the end realigns output when the input length is not a multiple of 3. Base64 is NOT encryption — it has no key and anyone can reverse it in milliseconds. Its only purpose is to safely carry binary data through systems that only accept printable text.</div>

                <div class="about-h">Why companies use it</div>
                <div class="about-li">Email and MIME: every file attachment you send is base64-encoded so binary data can travel over text-only mail protocols without corruption.</div>
                <div class="about-li">JWT tokens: the header and payload of every access token in OAuth 2.0 and OpenID Connect are base64url-encoded.</div>
                <div class="about-li">REST APIs: embedding images or binary blobs directly inside JSON responses avoids a separate file request.</div>
                <div class="about-li">Web assets: data URIs in HTML and CSS embed images inline without an extra HTTP round-trip, which is how this app serves the background photo.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

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
        # Build the character pool from selected sets and guarantee at least
        # one character from each. This prevents "all uppercase, no symbols" even
        # if the random fill happens to skip a category — a real weakness in
        # naive generators. Two-phase approach:
        #   Phase 1: pick one guaranteed character from each selected set.
        #   Phase 2: fill the rest randomly from the combined pool.
        #   Phase 3: shuffle so the guaranteed chars aren't always at the front.
        pool = ""
        required = []
        if g_upper:  pool += string.ascii_uppercase;  required.append(secrets.choice(string.ascii_uppercase))
        if g_lower:  pool += string.ascii_lowercase;  required.append(secrets.choice(string.ascii_lowercase))
        if g_digits: pool += string.digits;           required.append(secrets.choice(string.digits))
        if g_spec:   pool += SYMBOLS;                 required.append(secrets.choice(SYMBOLS))

        if not pool:
            st.warning("Select at least one character set.")
        else:
            padding  = [secrets.choice(pool) for _ in range(g_len - len(required))]
            combined = required + padding
            # secrets.SystemRandom() uses os.urandom() — the OS's CSPRNG.
            # This is critical: random.shuffle() uses a predictable seed and
            # would produce a guessable sequence. Never use random for security.
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

    with st.expander("📚 About this tool — examples, student uses, and why companies rely on it"):
        st.markdown(
            """
            <div class="about-wrap">
                <div class="about-h">What cybersecurity students can do with it</div>
                <div class="about-li">Build a password auditing script that reads a list of credentials from a breach dump and scores each one — a real task in penetration testing engagements.</div>
                <div class="about-li">Study NIST SP 800-63B, the US government's password guidelines. It actually recommends against forced complexity rules and instead emphasizes length and checking against known-breached passwords.</div>
                <div class="about-li">Understand entropy — a 16-character password using all four character sets has over 100 bits of entropy, making brute-force infeasible even with a GPU cluster.</div>
                <div class="about-li">Use the generator to create secure credentials for lab environments, CTF accounts, and any shared service where you need a one-time strong password.</div>

                <div class="about-h">Example</div>
                <div class="about-ex">
                    "Summer2024!"  →  Fair (has length and symbols but uses a common pattern)<br>
                    "kR#9mP@xW2!qN5vL"  →  Very Strong (all criteria met, 16 chars, fully random)<br><br>
                    At 10 billion guesses per second, cracking "Summer2024!" could take hours.<br>
                    Cracking "kR#9mP@xW2!qN5vL" would take longer than the age of the universe.
                </div>

                <div class="about-h">How it works</div>
                <div class="about-p">The analyzer checks eight criteria and scores them. The generator uses Python's secrets module, which reads from the operating system's cryptographically secure random number generator (CSPRNG) — the same source used for generating encryption keys. It is fundamentally different from the random module, which is only suitable for statistics. The generator seeds the pool, guarantees at least one character from each selected set, fills the remaining slots randomly, then shuffles the whole result to eliminate predictable patterns at the front.</div>

                <div class="about-h">Why companies use it</div>
                <div class="about-li">Password policy enforcement: organizations require minimum complexity for all employee accounts, and automated tooling validates compliance during provisioning.</div>
                <div class="about-li">Compliance: PCI-DSS, HIPAA, and SOC 2 Type II audits require documented password controls with evidence that weak credentials are prevented.</div>
                <div class="about-li">Privileged account management: service accounts, API keys, and admin credentials must be machine-generated, never human-chosen, and rotated on a schedule.</div>
                <div class="about-li">Security awareness: showing an employee a real-time score while they type is more effective than a policy document telling them what to do.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

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

    with st.expander("📚 About this tool — examples, student uses, and why companies rely on it"):
        st.markdown(
            """
            <div class="about-wrap">
                <div class="about-h">What cybersecurity students can do with it</div>
                <div class="about-li">Take a raw IP address from a server log or an IDS alert and immediately answer the first question a SOC analyst asks: where is this coming from and who owns it?</div>
                <div class="about-li">Identify attacker infrastructure — certain ISPs and ASNs are notorious for hosting bulletproof servers, Tor exit nodes, and botnets. Recognizing them on sight is a core threat hunting skill.</div>
                <div class="about-li">Build an enrichment pipeline: take the incident list from the Sentinel Dashboard, loop each source IP through this lookup, and produce a geo-tagged incident report automatically.</div>
                <div class="about-li">Investigate suspicious outbound connections on your own machine by looking up where a process is calling home.</div>

                <div class="about-h">Example</div>
                <div class="about-ex">
                    8.8.8.8         →  Google LLC, Mountain View, California, USA (known-good DNS)<br>
                    185.220.101.1   →  Tor exit relay, Nuremberg, Germany (known Tor infrastructure)<br>
                    45.155.205.233  →  Commonly seen in SSH brute-force campaigns, hosted on a bulletproof VPS
                </div>

                <div class="about-h">How it works</div>
                <div class="about-p">Every ISP that operates on the internet registers its IP address ranges with a Regional Internet Registry: ARIN covers North America, RIPE covers Europe, and APNIC covers Asia-Pacific. ip-api.com maintains a continuously updated database that maps these registered blocks to city-level geography and ISP metadata. When you submit an IP, the tool sends a single JSON request to their free API and parses the response — the same API the Sentinel Dashboard uses to enrich every detected incident automatically.</div>

                <div class="about-h">Why companies use it</div>
                <div class="about-li">SOC analysts enrich every security alert with IP reputation and geolocation before deciding whether to escalate — raw IPs alone have no context.</div>
                <div class="about-li">Firewalls and WAFs can block entire countries or autonomous systems as a rapid mitigation when an attack wave is traced to a single region or ISP.</div>
                <div class="about-li">Incident response: knowing the attacker's ISP and country helps determine whether an attack is targeted or opportunistic, and whether to notify law enforcement.</div>
                <div class="about-li">Threat intelligence platforms like Splunk and Microsoft Sentinel perform this lookup automatically on every event and store the results for correlation across incidents.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

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

    with st.expander("📚 About this tool — examples, student uses, and why companies rely on it"):
        st.markdown(
            """
            <div class="about-wrap">
                <div class="about-h">What cybersecurity students can do with it</div>
                <div class="about-li">Solve ROT13 challenges — one of the most common beginner-level CTF cipher problems. Many CTF platforms use ROT13 to hide hints and flag previews.</div>
                <div class="about-li">Demonstrate frequency analysis: because letters are only shifted and not scrambled, the most common letter in the ciphertext is still likely E in English — try to break a long encrypted message by analyzing letter frequency without knowing the shift.</div>
                <div class="about-li">Understand why simple ciphers fail: the Caesar cipher has exactly 25 possible keys. An attacker can brute-force every one by hand in minutes. This is the foundation for understanding what makes modern encryption strong.</div>
                <div class="about-li">Trace cryptographic history from Caesar to the Vigenere cipher to the Enigma machine to AES, and see how each generation closed the weaknesses of the previous one.</div>

                <div class="about-h">Example</div>
                <div class="about-ex">
                    Input: "ATTACK AT DAWN"   Shift: 13 (ROT13)<br>
                    Output: "NGGNPX NG QNJA"<br><br>
                    Input: "NGGNPX NG QNJA"   Shift: 13 (ROT13 again)<br>
                    Output: "ATTACK AT DAWN"  ← ROT13 is its own inverse (13 + 13 = 26)<br><br>
                    Classic Caesar: "THE QUICK BROWN FOX"  Shift: 3  →  "WKH TXLFN EURZQ IRA"
                </div>

                <div class="about-h">How it works</div>
                <div class="about-p">Each letter in the input is shifted forward in the alphabet by a fixed number, wrapping around at Z back to A. Numbers, spaces, and punctuation are left unchanged. To decode, shift in the opposite direction — or equivalently, shift forward by 26 minus the original shift. ROT13 uses shift 13, which means encoding and decoding are the same operation because 13 + 13 = 26 = one full rotation of the alphabet.</div>

                <div class="about-h">Why companies understand it matters</div>
                <div class="about-li">It directly teaches Kerckhoffs's principle: the security of a cipher must rest entirely in the key, not in keeping the algorithm secret. Caesar fails because the keyspace (25 possibilities) is trivially small, not because anyone knows the shift value.</div>
                <div class="about-li">ROT13 appears in real production code as a lightweight obfuscation for spoilers, easter eggs, and non-sensitive data in games, forums, and developer tools — not for security, but as a convention.</div>
                <div class="about-li">Security engineers use simple cipher examples in onboarding training to teach why weak cryptography is worse than no cryptography — it creates false confidence.</div>
                <div class="about-li">Understanding why substitution ciphers fail at scale (preserved letter frequency, tiny keyspace) is the direct intellectual path to understanding why AES uses substitution AND permutation AND multiple rounds — each step addressing a specific historical weakness.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
