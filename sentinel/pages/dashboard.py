import sys
import io
import gzip
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# tools/ lives in sentinel/, one level above pages/
sys.path.insert(0, str(Path(__file__).parent.parent))
from tools.parse_logs import parse_log_text
from tools.detect import run_all
from tools.ip_intel import enrich_incidents
from tools.report import generate_html_report

# ── Reset to navy theme (overrides any purple bleed from welcome page) ────────
st.markdown(
    """
    <style>
    [data-testid="stAppViewContainer"] {
        background: #07111f !important;
    }
    [data-testid="stSidebar"]        { background: #0c1e31 !important; }
    [data-testid="stSidebarContent"] { background: #0c1e31 !important; }
    [data-testid="stMetricValue"]    { font-size: 2rem; font-weight: 700; }
    .stTabs [data-baseweb="tab"]     { font-weight: 600; }
    </style>
    """,
    unsafe_allow_html=True,
)

SAMPLE_DIR = Path(__file__).parent.parent / "sample_logs"

_SEV_ICON  = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢", "info": "⚪"}
_SEV_COLOR = {
    "critical": "#ef4444", "high": "#f97316",
    "medium":   "#f59e0b", "low": "#22c55e", "info": "#6b7280",
}

# ── Sidebar controls ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Load Logs")
    mode = st.radio("Source", ["Sample logs", "Upload files"], horizontal=True)

    raw_text = ""
    if mode == "Upload files":
        uploaded = st.file_uploader(
            "Drop log files (.log .txt .gz)",
            type=["log", "txt", "gz"],
            accept_multiple_files=True,
        )
        if uploaded:
            for uf in uploaded:
                content = uf.read()
                if uf.name.endswith(".gz"):
                    content = gzip.decompress(content)
                raw_text += content.decode("utf-8", errors="replace") + "\n"
    else:
        if SAMPLE_DIR.exists():
            available = sorted(f.name for f in SAMPLE_DIR.glob("*.log"))
            chosen = st.multiselect("Select sample log(s)", available, default=available)
            for name in chosen:
                raw_text += (SAMPLE_DIR / name).read_text(encoding="utf-8", errors="replace") + "\n"
        else:
            st.warning("No sample_logs/ directory found.")

    st.divider()
    enrich_geo = st.toggle(
        "IP Geolocation",
        value=True,
        help="Live lookups via ip-api.com — 45 req/min, no key needed.",
    )
    run = st.button("Analyze", type="primary", use_container_width=True)

# ── Landing ───────────────────────────────────────────────────────────────────
if not run or not raw_text.strip():
    st.markdown("## 📊 Dashboard")
    st.info("Select log files in the sidebar, then click **Analyze** to run the threat-detection engine.")
    st.markdown("""
| Threat | Detection Rule |
|--------|---------------|
| SSH Brute Force | 5+ failed logins from same IP in 60 s |
| Credential Stuffing | 5+ distinct usernames from same IP |
| Privilege Escalation | sudo failures / root access |
| New OS Account | `useradd` events |
| SQL Injection | SQLi patterns in web request paths |
| Directory Traversal | `../` and encoded variants |
| XSS Attempts | `<script>`, `onerror=`, `javascript:` |
| Vulnerability Scanners | sqlmap, nikto, dirbuster, nmap… |
| Directory Brute Force | 10+ 404s from same IP in 10 s |
""")
    st.stop()

# ── Analysis ──────────────────────────────────────────────────────────────────
with st.spinner("Parsing logs…"):
    events = parse_log_text(raw_text)

with st.spinner("Running detection rules…"):
    incidents = run_all(events)

if enrich_geo and incidents:
    unique_src_ips = {i["source_ip"] for i in incidents if i.get("source_ip")}
    with st.spinner(f"Geolocating {len(unique_src_ips)} IP(s)…"):
        incidents = enrich_incidents(incidents)

# ── KPI row ───────────────────────────────────────────────────────────────────
n_crit = sum(1 for i in incidents if i.get("severity") == "critical")
n_high = sum(1 for i in incidents if i.get("severity") == "high")
n_med  = sum(1 for i in incidents if i.get("severity") == "medium")
n_src  = len({i["source_ip"] for i in incidents if i.get("source_ip")})

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Events Parsed", f"{len(events):,}")
c2.metric("Incidents",     len(incidents))
c3.metric("🔴 Critical",   n_crit)
c4.metric("🟠 High",       n_high)
c5.metric("🟡 Medium",     n_med)
c6.metric("Attacker IPs",  n_src)

st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_inc, tab_tl, tab_map, tab_raw = st.tabs(
    ["🚨 Incidents", "⏱ Timeline", "🗺 Attack Map", "📋 Raw Events"]
)

# ── Incidents ─────────────────────────────────────────────────────────────────
with tab_inc:
    if not incidents:
        st.success("No incidents detected in these logs.")
    else:
        rows = []
        for inc in incidents:
            geo = inc.get("geo", {})
            loc = f"{geo.get('city','')}, {geo.get('country','')}".strip(", ")
            ts  = inc.get("first_seen")
            sev = inc.get("severity", "info")
            rows.append({
                "Severity":   _SEV_ICON.get(sev, "⚪") + " " + sev.upper(),
                "Type":       inc.get("type", ""),
                "Source IP":  inc.get("source_ip") or "—",
                "Location":   loc or "—",
                "Count":      inc.get("count", 1),
                "First Seen": ts.strftime("%Y-%m-%d %H:%M:%S") if isinstance(ts, datetime) else "—",
                "Detail":     inc.get("detail", ""),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        st.caption(f"{len(incidents)} incident(s) across {n_src} attacker IP(s).")

        report_html = generate_html_report(incidents, events)
        st.download_button(
            "Download HTML Report",
            data=report_html.encode("utf-8"),
            file_name=f"sentinel_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
            mime="text/html",
        )

# ── Timeline ──────────────────────────────────────────────────────────────────
with tab_tl:
    timed = [i for i in incidents if isinstance(i.get("first_seen"), datetime)]
    if not timed:
        st.info("No timestamped incidents to plot.")
    else:
        df_t = pd.DataFrame([{
            "Incident": i["type"],
            "Start":    i["first_seen"],
            "End":      i.get("last_seen") or (i["first_seen"] + timedelta(seconds=5)),
            "Severity": i["severity"],
            "IP":       i.get("source_ip") or "N/A",
        } for i in timed])

        fig = px.timeline(
            df_t,
            x_start="Start", x_end="End",
            y="Incident", color="Severity",
            color_discrete_map=_SEV_COLOR,
            hover_data={"IP": True, "Start": False, "End": False},
            title="Incident Timeline",
        )
        fig.update_layout(
            plot_bgcolor="#07111f", paper_bgcolor="#07111f",
            font_color="#d8e4ef", title_font_color="#D4AF37",
            yaxis_title="", xaxis_title="",
            legend_title_text="Severity",
        )
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)

# ── Attack Map ────────────────────────────────────────────────────────────────
with tab_map:
    if not enrich_geo:
        st.info("Enable IP Geolocation in the sidebar to see the attack map.")
    else:
        pts = [
            {
                "lat":     inc["geo"].get("lat", 0),
                "lon":     inc["geo"].get("lon", 0),
                "ip":      inc.get("source_ip", ""),
                "country": inc.get("geo", {}).get("country", ""),
                "type":    inc.get("type", ""),
                "sev":     inc.get("severity", "info"),
            }
            for inc in incidents
            if inc.get("geo")
            and inc["geo"].get("lat")
            and (inc["geo"]["lat"], inc["geo"]["lon"]) != (0.0, 0.0)
        ]
        if not pts:
            st.info(
                "No geolocation data — ip-api.com doesn't resolve RFC-5737 "
                "documentation IPs used in the sample logs. Upload real logs to see this map."
            )
        else:
            df_geo = pd.DataFrame(pts)
            fig = px.scatter_geo(
                df_geo, lat="lat", lon="lon",
                color="sev", color_discrete_map=_SEV_COLOR,
                hover_data={"ip": True, "country": True, "type": True, "lat": False, "lon": False},
                size_max=14,
                projection="natural earth",
                title="Attack Origin Map",
            )
            fig.update_layout(
                geo=dict(
                    bgcolor="#07111f", showland=True, landcolor="#0c1e31",
                    showocean=True, oceancolor="#07111f",
                    showcountries=True, countrycolor="#1a2e42",
                ),
                plot_bgcolor="#07111f", paper_bgcolor="#07111f",
                font_color="#d8e4ef", title_font_color="#D4AF37",
            )
            st.plotly_chart(fig, use_container_width=True)

# ── Raw Events ────────────────────────────────────────────────────────────────
with tab_raw:
    if not events:
        st.info("No events parsed.")
    else:
        df_e = pd.DataFrame([{
            "Timestamp":  str(e.get("timestamp", "")),
            "Type":       e.get("event_type", ""),
            "Source IP":  e.get("source_ip") or "—",
            "User":       e.get("user") or "—",
            "Process":    e.get("process") or "—",
            "Message":    e.get("message", ""),
        } for e in events])

        fc1, fc2 = st.columns([2, 3])
        with fc1:
            types     = ["All"] + sorted(df_e["Type"].unique().tolist())
            filt_type = st.selectbox("Event type", types, key="raw_type")
        with fc2:
            filt_ip = st.text_input("Source IP contains", key="raw_ip")

        if filt_type != "All":
            df_e = df_e[df_e["Type"] == filt_type]
        if filt_ip.strip():
            df_e = df_e[df_e["Source IP"].str.contains(filt_ip.strip(), na=False)]

        st.caption(f"Showing {len(df_e):,} of {len(events):,} events")
        st.dataframe(df_e, use_container_width=True, hide_index=True)
