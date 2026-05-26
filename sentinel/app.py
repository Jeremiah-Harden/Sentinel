import base64
from pathlib import Path
import streamlit as st

st.set_page_config(
    page_title="Sentinel",
    page_icon="🛡",
    layout="wide",
    initial_sidebar_state="expanded",
)

def _img_b64(name: str) -> str:
    p = Path(__file__).parent / "assets" / name
    try:
        ext = p.suffix.lstrip(".")
        return f"data:image/{ext};base64," + base64.b64encode(p.read_bytes()).decode()
    except Exception:
        return ""

_photo = _img_b64("jeremiah.png")

with st.sidebar:
    st.markdown(
        """
        <div style="text-align:center;padding:1rem 0 0.5rem;">
            <span style="font-size:2rem;">🛡</span><br>
            <span style="color:#BF5FFF;font-size:1.2rem;font-weight:900;letter-spacing:0.2em;">SENTINEL</span><br>
            <span style="color:#6b5a8a;font-size:0.72rem;letter-spacing:0.12em;">SECURITY OPERATIONS</span>
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

pg = st.navigation(
    [
        st.Page("pages/welcome.py",   title="Home",      icon="🏠", default=True),
        st.Page("pages/dashboard.py", title="Dashboard", icon="📊"),
    ],
    position="sidebar",
)
pg.run()
