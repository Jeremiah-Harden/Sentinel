import base64
from pathlib import Path
import streamlit as st

_bg_path = Path(__file__).parent.parent / "assets" / "atlanta.jpg"
try:
    _bg_b64 = base64.b64encode(_bg_path.read_bytes()).decode()
except Exception:
    _bg_b64 = ""

# ── Background + sidebar (f-string — needs base64 variable) ──────────────────
st.markdown(
    f"""
    <style>
    [data-testid="stAppViewContainer"] {{
        background-image:
            linear-gradient(rgba(0,0,0,0.62), rgba(0,0,0,0.62)),
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

# ── All other CSS classes ─────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* ── Hero ── */
    .hero-wrap { text-align:center; padding: 3.5rem 1rem 2rem; }
    .hero-title {
        font-size: clamp(3rem, 8vw, 6rem);
        font-weight: 900;
        background: linear-gradient(135deg, #00d4ff 0%, #ffffff 50%, #00d4ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        filter: drop-shadow(0 0 20px rgba(0,212,255,0.5)) drop-shadow(0 0 55px rgba(0,212,255,0.25));
        letter-spacing: 0.45em;
        line-height: 1;
        margin: 0;
    }
    .hero-sub {
        font-size: 0.95rem;
        color: #88bbcc;
        letter-spacing: 0.28em;
        text-transform: uppercase;
        margin-top: 0.6rem;
    }
    .hero-line {
        width: 220px;
        height: 1px;
        background: linear-gradient(90deg, transparent, #00d4ff, transparent);
        margin: 1.4rem auto 0;
    }

    /* ── Cloud card ── */
    .cloud-card {
        background: linear-gradient(135deg, rgba(0,25,45,0.92) 0%, rgba(0,15,30,0.92) 60%, rgba(0,20,40,0.92) 100%);
        border: 1px solid rgba(0,212,255,0.22);
        box-shadow: 0 0 40px rgba(0,212,255,0.07), 0 0 80px rgba(0,212,255,0.03), 0 12px 40px rgba(0,0,0,0.65);
        border-radius: 18px;
        padding: 0;
        overflow: hidden;
        position: relative;
    }
    .cloud-card::before {
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent, #00d4ff, transparent);
    }
    .cloud-header {
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 1.4rem 2rem;
        background: linear-gradient(90deg, rgba(0,30,50,0.97) 0%, rgba(0,20,40,0.97) 100%);
        border-bottom: 1px solid rgba(0,212,255,0.12);
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
        color: #5588aa;
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
        box-shadow: 0 0 8px #4ade80;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; box-shadow: 0 0 8px #4ade80; }
        50%       { opacity: 0.45; box-shadow: 0 0 3px #4ade80; }
    }
    .cloud-body { padding: 1.5rem 2rem; }
    .cap-row {
        display: flex;
        align-items: flex-start;
        gap: 0.8rem;
        padding: 0.6rem 0;
        border-bottom: 1px solid rgba(0,212,255,0.07);
        color: #c0d8e8;
        font-size: 0.91rem;
    }
    .cap-row:last-child { border-bottom: none; }
    .cap-check { color: #00d4ff; font-weight: 700; flex-shrink: 0; font-size: 1rem; }
    .cap-icon  { flex-shrink: 0; }

    /* ── Roadmap cards ── */
    .road-card {
        background: rgba(0,15,30,0.88);
        border: 1px solid #152535;
        border-top: 2px solid var(--accent, #00d4ff);
        border-radius: 14px;
        padding: 1.4rem 1.2rem;
        height: 100%;
        position: relative;
        transition: border-color 0.2s, box-shadow 0.2s, transform 0.15s;
    }
    .road-card:hover {
        border-color: var(--accent, #00d4ff);
        box-shadow: 0 0 20px rgba(0,212,255,0.1);
        transform: translateY(-2px);
    }
    .road-icon  { font-size: 2rem; margin-bottom: 0.6rem; }
    .road-title { color: #ffffff; font-size: 0.9rem; font-weight: 700; margin-bottom: 0.35rem; }
    .road-desc  { color: #5588aa; font-size: 0.79rem; line-height: 1.5; }
    .soon-tag {
        position: absolute;
        top: 0.7rem; right: 0.7rem;
        background: #111a22;
        border: 1px solid #2a3d50;
        border-radius: 8px;
        padding: 0.12rem 0.55rem;
        font-size: 0.65rem;
        color: #5588aa;
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

# ── Feature card ──────────────────────────────────────────────────────────────
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

col_a, col_b, _ = st.columns([1, 1, 4])
with col_a:
    if st.button("Launch Dashboard →", type="primary", use_container_width=True):
        st.switch_page("pages/dashboard.py")
with col_b:
    if st.button("⚡ Cyber Tools", use_container_width=True):
        st.switch_page("pages/tools.py")

st.divider()

# ── Roadmap ───────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div style="text-align:center;margin:0.5rem 0 1.5rem;">
        <div style="color:#ffffff;font-size:1.1rem;font-weight:800;letter-spacing:0.15em;text-transform:uppercase;">
            Feature Roadmap
        </div>
        <div style="color:#445566;font-size:0.82rem;margin-top:0.3rem;">
            Ideas to make Sentinel more powerful — all achievable with free tools
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

ACCENTS = ["#00d4ff", "#a855f7", "#4ade80", "#f97316", "#3b82f6",
           "#f59e0b", "#ef4444", "#06b6d4", "#8b5cf6", "#10b981"]

IDEAS = [
    ("🎯", "MITRE ATT&CK Mapping",   "Map every detected incident to a real ATT&CK technique and tactic — turns raw alerts into a kill-chain story.",          "Soon"),
    ("🕵️", "Threat Intel Feed",       "Live IOC checking against AbuseIPDB and AlienVault OTX — know if an IP is already known-bad before it hits your logs.", "Free"),
    ("📡", "Real-time Log Streaming", "Tail a live log file and stream new events into the dashboard as they happen — no reload needed.",                        "Soon"),
    ("🔔", "Smart Alert System",      "Send Email or Slack notifications the moment a critical incident is detected — instant response, no manual watching.",    "Free"),
    ("📈", "Historical Trending",     "Store past scan results and chart incident counts over time — spot patterns, compare weeks, show progress.",              "Soon"),
    ("🌐", "Network PCAP Analysis",   "Upload a .pcap file and auto-detect port scans, ARP spoofing, and unusual traffic patterns using Scapy.",                "Soon"),
    ("🔑", "Password Breach Checker", "Check exposed credentials from your logs against Have I Been Pwned — identify compromised accounts instantly.",          "Free"),
    ("📋", "Compliance Reporting",    "Automatically map incidents to NIST CSF and CIS Controls — generate a compliance gap report in one click.",             "Soon"),
    ("🛡️", "CVE Intelligence",        "Cross-reference server software versions found in logs against the NVD — surface active vulnerabilities immediately.",  "Free"),
    ("🌑", "Dark Web IOC Monitor",    "Check IPs, domains, and emails against public paste sites and breach databases — know when your assets leak.",          "Soon"),
]

rows = [IDEAS[:5], IDEAS[5:]]
for row_idx, row in enumerate(rows):
    cols = st.columns(5, gap="small")
    for i, (col, (icon, title, desc, tag)) in enumerate(zip(cols, row)):
        accent = ACCENTS[row_idx * 5 + i]
        tag_class = "free-tag" if tag == "Free" else "soon-tag"
        col.markdown(
            f"""
            <div class="road-card" style="--accent:{accent};">
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
    <div style="text-align:center;color:#223344;font-size:0.75rem;margin-top:1rem;letter-spacing:0.1em;">
        Built with Streamlit · Python · Playwright · BeautifulSoup · Plotly
    </div>
    """,
    unsafe_allow_html=True,
)
