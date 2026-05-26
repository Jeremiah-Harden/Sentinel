import streamlit as st

st.set_page_config(
    page_title="Sentinel",
    page_icon="🛡",
    layout="wide",
    initial_sidebar_state="expanded",
)

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

pg = st.navigation(
    [
        st.Page("pages/welcome.py",   title="Home",      icon="🏠", default=True),
        st.Page("pages/dashboard.py", title="Dashboard", icon="📊"),
    ],
    position="sidebar",
)
pg.run()
