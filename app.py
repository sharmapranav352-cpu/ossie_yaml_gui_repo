import streamlit as st

from utils.branding import apply_branding, brand_block, icon_path, progress_rail
from utils.navigation import PAGES
from utils.state import init_state

st.set_page_config(
    page_title="Semantic Model Builder | Snap Analytics",
    page_icon=icon_path() or ":material/hub:",
    layout="wide",
)

init_state()
apply_branding()

nav = st.navigation(
    [
        st.Page(p["path"], title=p["title"], icon=p["icon"], default=(i == 0))
        for i, p in enumerate(PAGES)
    ]
)

brand_block()
progress_rail(nav.title)
nav.run()
