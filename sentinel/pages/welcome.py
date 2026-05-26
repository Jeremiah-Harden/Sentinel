import base64
from pathlib import Path
import streamlit as st

_bg_path = Path(__file__).parent.parent / "assets" / "atlanta.jpg"
_bg_b64  = base64.b64encode(_bg_path.read_bytes()).decode()

# ── Background + sidebar (f-string — needs base64 variable) ──────────────────
st.markdown(
    f"""
    <style>
    [data-testid="stAppViewContainer"] {{
        background-image:
            linear-gradient(rgba(0,0,0,0.58), rgba(0,0,0,0.58)),
            url("data:image/jpeg;base64,{_bg_b64}") !important;
        background-size: cover !important;
        background-position: center !important;
        background-attachment: fixed !important;
    }}
    [data-testid="stSidebar"]        {{ background: #0d0d0d !important; }}
    [data-testid="stSidebarContent"] {{ background: #0d0d0d !important; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ── All other CSS classes (regular string — no escaping needed) ───────────────
st.markdown(
    """
    <style>
    /* ── Hero ── */
    .hero-wrap { text-align:center; padding: 3.5rem 1rem 1.5rem; }
    .hero-title {
        font-size: clamp(3rem, 8vw, 6rem);
        font-weight: 900;
        color: #ffffff;
        text-shadow: 0 0 8px #ffffff, 0 0 25px #cccccc, 0 0 55px #888888;
        letter-spacing: 0.45em;
        line-height: 1;
        margin: 0;
    }
    .hero-sub {
        font-size: 0.95rem;
        color: #cccccc;
        letter-spacing: 0.28em;
        text-transform: uppercase;
        margin-top: 0.6rem;
    }
    .hero-line {
        width: 220px;
        height: 1px;
        background: linear-gradient(90deg, transparent, #ffffff, transparent);
        margin: 1.4rem auto 0;
    }

    /* ── Cloud card ── */
    .cloud-card {
        background: linear-gradient(135deg, rgba(17,17,17,0.88) 0%, rgba(26,26,26,0.88) 60%, rgba(13,13,13,0.88) 100%);
        border: 1px solid #444444;
        box-shadow: 0 0 35px rgba(255,255,255,0.05), 0 12px 40px rgba(0,0,0,0.6);
        border-radius: 18px;
        padding: 0;
        overflow: hidden;
        position: relative;
    }
    .cloud-card::after {
        content: "☁";
        position: absolute;
        bottom: -50px; right: -25px;
        font-size: 18rem;
        opacity: 0.03;
        color: #ffffff;
        line-height: 1;
        pointer-events: none;
    }
    .cloud-header {
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 1.4rem 2rem;
        background: linear-gradient(90deg, rgba(26,26,26,0.95) 0%, rgba(17,17,17,0.95) 100%);
        border-bottom: 1px solid #33333344;
    }
    .cloud-logo { font-size: 2.2rem; line-height: 1; }
    .cloud-service { flex: 1; }
    .cloud-service-name {
        color: #ffffff;
        font-size: 1.1rem;
        font-weight: 700;
        letter-spacing: 0.06em;
    }
    .cloud-service-tag {
        color: #888888;
        font-size: 0.75rem;
        letter-spacing: 0.08em;
        margin-top: 2px;
    }
    .status-badge {
        display: flex;
        align-items: center;
        gap: 0.4rem;
        background: #0d3320;
        border: 1px solid #1a6640;
        border-radius: 20px;
        padding: 0.3rem 0.9rem;
        font-size: 0.73rem;
        color: #4ade80;
        white-space: nowrap;
    }
    .status-dot {
        width: 7px; height: 7px;
        border-radius: 50%;
        background: #4ade80;
        box-shadow: 0 0 6px #4ade80;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50%       { opacity: 0.4; }
    }
    .cloud-body { padding: 1.5rem 2rem; }
    .cap-row {
        display: flex;
        align-items: flex-start;
        gap: 0.8rem;
        padding: 0.55rem 0;
        border-bottom: 1px solid #2a2a2a;
        color: #dddddd;
        font-size: 0.91rem;
    }
    .cap-row:last-child { border-bottom: none; }
    .cap-check { color: #ffffff; font-weight: 700; flex-shrink: 0; font-size: 1rem; }
    .cap-icon  { flex-shrink: 0; }

    /* ── Roadmap cards ── */
    .road-card {
        background: rgba(17,17,17,0.85);
        border: 1px solid #333333;
        border-radius: 14px;
        padding: 1.4rem 1.2rem;
        height: 100%;
        position: relative;
        transition: border-color 0.2s, box-shadow 0.2s;
    }
    .road-card:hover {
        border-color: #888888;
        box-shadow: 0 0 18px rgba(255,255,255,0.1);
    }
    .road-icon  { font-size: 2rem; margin-bottom: 0.6rem; }
    .road-title { color: #ffffff; font-size: 0.9rem; font-weight: 700; margin-bottom: 0.35rem; }
    .road-desc  { color: #888888; font-size: 0.79rem; line-height: 1.5; }
    .soon-tag {
        position: absolute;
        top: 0.7rem; right: 0.7rem;
        background: #1a1a1a;
        border: 1px solid #444444;
        border-radius: 8px;
        padding: 0.12rem 0.55rem;
        font-size: 0.65rem;
        color: #888888;
    }
    .free-tag {
        position: absolute;
        top: 0.7rem; right: 0.7rem;
        background: #0d2a1a;
        border: 1px solid #166534;
        border-radius: 8px;
        padding: 0.12rem 0.55rem;
        font-size: 0.65rem;
        color: #4ade80;
    }

    /* hide default Streamlit top padding */
    .block-container { padding-top: 0 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="hero-wrap">
        <div class="hero-title">SENTINEL</div>
        <div class="hero-sub">Security Incident Dashboard &nbsp;·&nbsp; Powered by Python</div>
        <div class="hero-line"></div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Cloud card ────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="cloud-card">
        <div class="cloud-header">
            <div class="cloud-logo">☁️</div>
            <div class="cloud-service">
                <div class="cloud-service-name">Sentinel Cloud Dashboard</div>
                <div class="cloud-service-tag">Security Operations &nbsp;·&nbsp; Log Intelligence &nbsp;·&nbsp; Threat Detection &nbsp;·&nbsp; v1.0</div>
            </div>
            <div class="status-badge">
                <div class="status-dot"></div>
                OPERATIONAL
            </div>
        </div>
        <div class="cloud-body">
            <div class="cap-row"><span class="cap-check">✓</span><span class="cap-icon">📂</span>
                <span>Parse <b>SSH auth.log</b>, <b>syslog</b>, <b>Apache</b> &amp; <b>Nginx</b> access logs — upload your own or use built-in sample data</span>
            </div>
            <div class="cap-row"><span class="cap-check">✓</span><span class="cap-icon">🚨</span>
                <span>Detect <b>9 threat types</b> automatically: SSH brute force, credential stuffing, SQLi, XSS, directory traversal, vulnerability scanners, privilege escalation, and more</span>
            </div>
            <div class="cap-row"><span class="cap-check">✓</span><span class="cap-icon">🌍</span>
                <span>Geolocate attacking IPs in real-time using <b>ip-api.com</b> — free, no API key required</span>
            </div>
            <div class="cap-row"><span class="cap-check">✓</span><span class="cap-icon">🗺️</span>
                <span>Visualize threat origins on an <b>interactive world map</b> with severity color-coding</span>
            </div>
            <div class="cap-row"><span class="cap-check">✓</span><span class="cap-icon">⏱️</span>
                <span>View a <b>Gantt-style incident timeline</b> showing when and how attacks unfolded</span>
            </div>
            <div class="cap-row"><span class="cap-check">✓</span><span class="cap-icon">📄</span>
                <span>Download a self-contained <b>HTML security report</b> — ready to present or share</span>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<br>", unsafe_allow_html=True)

if st.button("Launch Dashboard →", type="primary", use_container_width=False):
    st.switch_page("pages/dashboard.py")

st.divider()

# ── Roadmap ───────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div style="text-align:center;margin:0.5rem 0 1.5rem;">
        <div style="color:#ffffff;font-size:1.1rem;font-weight:800;letter-spacing:0.15em;text-transform:uppercase;">
            Feature Roadmap
        </div>
        <div style="color:#666666;font-size:0.82rem;margin-top:0.3rem;">
            Ideas to make Sentinel more powerful — all achievable with free tools
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

IDEAS = [
    ("🎯", "MITRE ATT&CK Mapping",      "Map every detected incident to a real ATT&CK technique and tactic — turns raw alerts into a kill-chain story.",          "Soon"),
    ("🕵️", "Threat Intel Feed",          "Live IOC checking against AbuseIPDB and AlienVault OTX — know if an IP is already known-bad before it hits your logs.", "Free"),
    ("📡", "Real-time Log Streaming",    "Tail a live log file and stream new events into the dashboard as they happen — no reload needed.",                        "Soon"),
    ("🔔", "Smart Alert System",         "Send Email or Slack notifications the moment a critical incident is detected — instant response, no manual watching.",    "Free"),
    ("📈", "Historical Trending",        "Store past scan results and chart incident counts over time — spot patterns, compare weeks, show progress.",              "Soon"),
    ("🌐", "Network PCAP Analysis",      "Upload a .pcap file and auto-detect port scans, ARP spoofing, and unusual traffic patterns using Scapy.",                "Soon"),
    ("🔑", "Password Breach Checker",    "Check exposed credentials from your logs against Have I Been Pwned — identify compromised accounts instantly.",          "Free"),
    ("📋", "Compliance Reporting",       "Automatically map incidents to NIST CSF and CIS Controls — generate a compliance gap report in one click.",             "Soon"),
    ("🛡️", "CVE Intelligence",           "Cross-reference server software versions found in logs against the NVD — surface active vulnerabilities immediately.",  "Free"),
    ("🌑", "Dark Web IOC Monitor",       "Check IPs, domains, and emails against public paste sites and breach databases — know when your assets leak.",          "Soon"),
]

rows = [IDEAS[:5], IDEAS[5:]]
for row in rows:
    cols = st.columns(5, gap="small")
    for col, (icon, title, desc, tag) in zip(cols, row):
        tag_class = "free-tag" if tag == "Free" else "soon-tag"
        col.markdown(
            f"""
            <div class="road-card">
                <div class="{tag_class}">{tag}</div>
                <div class="road-icon">{icon}</div>
                <div class="road-title">{title}</div>
                <div class="road-desc">{desc}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("<br>", unsafe_allow_html=True)

st.markdown(
    """
    <div style="text-align:center;color:#444444;font-size:0.75rem;margin-top:1rem;letter-spacing:0.1em;">
        Built with Streamlit · Python · Playwright · BeautifulSoup · Plotly
    </div>
    """,
    unsafe_allow_html=True,
)
