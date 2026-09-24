import streamlit as st

from utils.branding import (
    apply_branding,
    brand_block,
    editing_banner,
    icon_path,
    progress_rail,
)
from utils.navigation import PAGES
from utils.state import init_state

st.set_page_config(
    page_title="Project Compass | Semantic Model Builder",
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

brand_block(show_logo=(nav.title == "Connect"))
progress_rail(nav.title)
editing_banner()
nav.run()
