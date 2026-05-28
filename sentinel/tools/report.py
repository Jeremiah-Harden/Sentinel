"""
report.py — HTML security report generator for Sentinel.

Produces a self-contained HTML file (no external dependencies) that an analyst
can download, email, or present directly. All styling is inline so it renders
correctly offline and in email clients.

Why HTML instead of PDF?
  HTML is universally viewable (no reader software needed), easy to generate
  in Python without heavy dependencies, and remains readable even if the
  styling breaks. For a portfolio project, a downloadable HTML report also
  demonstrates that you understand web structure.

Security note: _html.escape() is applied to ALL user-supplied data (IP addresses,
incident types, detail strings) before injection into the HTML template.
This prevents stored XSS if a malicious payload in a log file were to end up
in the report — a real concern in security tooling.
"""

import html as _html
from datetime import datetime

# Severity → color mapping (same palette as the Streamlit UI for consistency)
_SEV_COLOR = {
    "critical": "#ef4444",
    "high":     "#f97316",
    "medium":   "#f59e0b",
    "low":      "#22c55e",
    "info":     "#6b7280",
}


def _row(inc: dict, idx: int) -> str:
    """Render one incident as an HTML <tr> table row.

    idx is the 1-based row number (displayed as "#" in the report).
    All dynamic strings go through _html.escape() before insertion — this is
    non-negotiable for any tool that processes attacker-controlled data.
    """
    sev    = inc.get("severity", "info")
    color  = _SEV_COLOR.get(sev, "#6b7280")
    ip     = _html.escape(inc.get("source_ip") or "N/A")
    geo    = inc.get("geo", {})
    # Combine city and country; strip leading/trailing ", " if one is empty
    loc    = f"{geo.get('city','')}, {geo.get('country','')}".strip(", ")
    ts     = inc.get("first_seen")
    ts_s   = ts.strftime("%Y-%m-%d %H:%M:%S") if isinstance(ts, datetime) else "N/A"
    detail = _html.escape(inc.get("detail", ""))
    label  = _html.escape(inc.get("type", ""))

    return (
        f"<tr>"
        f"<td>{idx}</td>"
        f'<td><span style="color:{color};font-weight:bold">{sev.upper()}</span></td>'
        f"<td>{label}</td>"
        f"<td>{ip}</td>"
        f"<td>{_html.escape(loc)}</td>"
        f"<td>{ts_s}</td>"
        f'<td style="font-size:.82em;color:#9ca3af">{detail}</td>'
        f"</tr>"
    )


def generate_html_report(
    incidents: list[dict],
    events: list[dict],
    title: str = "Sentinel Security Report",
) -> str:
    """Build a complete, self-contained HTML security report.

    The report includes:
      - Metadata: generation time, event count, incident count
      - KPI grid: critical / high / medium / total counts (styled with severity colors)
      - Incident table: one row per incident, sorted by the caller (run_all sorts by severity)

    The `events` list is used only for the "Events analyzed" count in metadata —
    it's not iterated for the report body (incidents already contain the summaries).

    Returns the HTML string. The caller (dashboard.py) encodes it to bytes and
    serves it as a file download via st.download_button.
    """
    now    = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Build all table rows first, then join — avoids O(n²) string concatenation
    rows   = "".join(_row(inc, i + 1) for i, inc in enumerate(incidents))
    n_crit = sum(1 for i in incidents if i.get("severity") == "critical")
    n_high = sum(1 for i in incidents if i.get("severity") == "high")
    n_med  = sum(1 for i in incidents if i.get("severity") == "medium")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{_html.escape(title)}</title>
<style>
body{{font-family:'Segoe UI',sans-serif;background:#07111f;color:#d8e4ef;margin:0;padding:2rem}}
h1{{color:#D4AF37;border-bottom:2px solid #D4AF37;padding-bottom:.5rem}}
.meta{{color:#6b7280;font-size:.85em;margin-bottom:2rem}}
.grid{{display:flex;gap:1rem;margin-bottom:2rem}}
.stat{{background:#0c1e31;border-radius:8px;padding:1rem 2rem;text-align:center;flex:1}}
.stat .n{{font-size:2.5rem;font-weight:bold}}
.stat .l{{font-size:.8rem;color:#6b7280}}
table{{width:100%;border-collapse:collapse}}
th{{background:#0c1e31;color:#D4AF37;text-align:left;padding:.6rem .8rem;font-size:.85em}}
td{{padding:.55rem .8rem;border-bottom:1px solid #1a2e42;font-size:.85em;vertical-align:top}}
tr:hover td{{background:#0c1e31}}
</style>
</head>
<body>
<h1>🛡 Sentinel — Security Incident Report</h1>
<p class="meta">Generated: {now} &nbsp;|&nbsp; Events analyzed: {len(events):,} &nbsp;|&nbsp; Incidents: {len(incidents)}</p>
<div class="grid">
  <div class="stat"><div class="n" style="color:#ef4444">{n_crit}</div><div class="l">CRITICAL</div></div>
  <div class="stat"><div class="n" style="color:#f97316">{n_high}</div><div class="l">HIGH</div></div>
  <div class="stat"><div class="n" style="color:#f59e0b">{n_med}</div><div class="l">MEDIUM</div></div>
  <div class="stat"><div class="n">{len(incidents)}</div><div class="l">TOTAL</div></div>
</div>
<table>
<thead><tr>
  <th>#</th><th>Severity</th><th>Incident Type</th>
  <th>Source IP</th><th>Location</th><th>First Seen</th><th>Detail</th>
</tr></thead>
<tbody>{rows}</tbody>
</table>
</body>
</html>"""
