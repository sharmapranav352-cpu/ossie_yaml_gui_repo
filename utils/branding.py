"""
Look and feel for the app: header, step navigation, page titles, action bar.

Colours come from .streamlit/config.toml, so the brand colour is set in one
place. Logos are read from the assets/ folder (see assets/README.md):
  compass_logo  top of the front page (and the browser tab icon)
  snap_logo     bottom-right corner of every page
"""

import base64
import html
import mimetypes
from pathlib import Path

import streamlit as st

from services.builders import validate
from utils.navigation import BY_KEY, PAGES

PROJECT = "Project Compass"
PRODUCT = "Semantic Model Builder"
COMPANY = "Snap Analytics"

ASSETS = Path("assets")


##################################################
# LOGOS
##################################################

def _first_existing(*names):
    for name in names:
        path = ASSETS / name
        if path.exists():
            return str(path)
    return None


def snap_logo_path():
    return _first_existing(
        "snap_logo.svg", "snap_logo.png", "snap_logo.webp", "snap_logo.jpg"
    )


def compass_logo_path():
    return _first_existing(
        "compass_logo.svg", "compass_logo.png", "compass_logo.webp", "compass_logo.jpg"
    )


def icon_path():
    return _first_existing("compass_icon.png", "compass_icon.svg") or compass_logo_path()


def _img_tag(path, alt):
    mime = mimetypes.guess_type(path)[0] or "image/png"
    if path.endswith(".svg"):
        mime = "image/svg+xml"
    elif path.endswith(".webp"):
        mime = "image/webp"
    data = base64.b64encode(Path(path).read_bytes()).decode()
    return f'<img src="data:{mime};base64,{data}" alt="{html.escape(alt)}">'


##################################################
# GLOBAL STYLE
##################################################

def _css():
    primary = st.get_option("theme.primaryColor") or "#0A6FA8"
    ink = st.get_option("theme.textColor") or "#17263A"
    line = st.get_option("theme.borderColor") or "#D8E0E8"
    surface = st.get_option("theme.secondaryBackgroundColor") or "#F3F6F9"

    return f"""
<style>
:root {{
  --cx-primary: {primary};
  --cx-ink: {ink};
  --cx-line: {line};
  --cx-surface: {surface};
  --cx-muted: #5A6878;
  --cx-done: #217A4F;
  --cx-warn: #9A5B00;
}}

/* ---------- Frame: no sidebar, one centred column ---------- */
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"],
[data-testid="stSidebarNav"], [data-testid="stDecoration"], footer {{
  display: none !important;
}}
.block-container {{
  max-width: 100%;
  padding-left: 3rem;
  padding-right: 3rem;
  padding-top: 3.25rem;
  padding-bottom: 6rem;
}}
h1 {{ letter-spacing: -0.015em; }}
h2, h3 {{ letter-spacing: -0.005em; }}

/* ---------- Header ---------- */
.cx-header {{
  display: flex; align-items: center; justify-content: space-between;
  gap: 1rem; flex-wrap: wrap; margin-bottom: 1.25rem;
}}
.cx-brand {{
  display: flex; align-items: center; gap: .75rem; min-width: 0;
  color: var(--cx-muted); font-size: .9375rem; font-weight: 500;
}}
.cx-brand img {{ height: 64px; width: auto; display: block; }}
.cx-brand .cx-wordmark {{
  color: var(--cx-ink); font-weight: 700; font-size: 1.375rem;
  letter-spacing: -0.02em; white-space: nowrap;
}}
.cx-brand .cx-divider {{ width: 1px; height: 28px; background: var(--cx-line); }}
.cx-pills {{ display: flex; gap: .5rem; flex-wrap: wrap; }}
.cx-pill {{
  display: inline-flex; align-items: center; gap: .4rem;
  padding: .3rem .7rem; border-radius: 999px;
  border: 1px solid var(--cx-line); background: #fff;
  font-size: .8125rem; font-weight: 500; color: var(--cx-muted);
  white-space: nowrap;
}}
.cx-pill b {{ color: var(--cx-ink); font-weight: 600; }}
.cx-dot {{ width: .5rem; height: .5rem; border-radius: 50%; background: #B8C2CC; }}
.cx-pill.is-ok .cx-dot {{ background: var(--cx-done); }}

/* ---------- Step navigation ---------- */
.st-key-cx-rail {{
  border-bottom: 1px solid var(--cx-line); margin-bottom: 2rem; gap: 0;
}}
.st-key-cx-rail [data-testid="stHorizontalBlock"] {{ gap: 0; }}
[class*="st-key-cx-step-"] {{
  gap: 0; padding: 0 .5rem .625rem 0; margin-bottom: -1px;
  border-bottom: 3px solid transparent;
}}
[class*="st-key-cx-step-"][class*="-current"] {{ border-bottom-color: var(--cx-primary); }}
[class*="st-key-cx-step-"] [data-testid="stPageLink"] a {{
  padding: .25rem .25rem .125rem 0; background: transparent !important;
  border-radius: .25rem;
}}
[class*="st-key-cx-step-"] [data-testid="stPageLink"] a {{ cursor: pointer; }}
[class*="st-key-cx-step-"] [data-testid="stPageLink"] a:hover p {{
  color: var(--cx-primary); text-decoration: underline; text-underline-offset: 3px;
}}
[class*="st-key-cx-step-"] [data-testid="stPageLink"] p {{
  font-weight: 600; font-size: .9375rem; color: var(--cx-ink);
  white-space: nowrap;
}}
[class*="st-key-cx-step-"] [data-testid="stIconMaterial"] {{
  color: #9AA6B2; font-size: 1.375rem;
}}
[class*="st-key-cx-step-"][class*="-done"] [data-testid="stIconMaterial"] {{ color: var(--cx-done); }}
[class*="st-key-cx-step-"][class*="-warn"] [data-testid="stIconMaterial"] {{ color: var(--cx-warn); }}
[class*="st-key-cx-step-"][class*="-current"] [data-testid="stIconMaterial"] {{ color: var(--cx-primary); }}
[class*="st-key-cx-step-"] [data-testid="stMarkdown"],
[class*="st-key-cx-step-"] [data-testid="stMarkdownContainer"] {{ margin: 0; }}
.cx-step-status {{
  font-size: .8125rem; color: var(--cx-muted); line-height: 1.3;
  padding: 0 0 .375rem 1.875rem; margin: 0; white-space: nowrap;
  overflow: hidden; text-overflow: ellipsis;
}}
[class*="st-key-cx-step-"][class*="-warn"] .cx-step-status {{ color: var(--cx-warn); }}

/* ---------- Page title ---------- */
.cx-title {{ margin: 0 0 1.5rem; max-width: 46rem; }}
.cx-title h1 {{ margin: 0 0 .375rem; padding: 0; line-height: 1.2; }}
.cx-title p {{ margin: 0; color: var(--cx-muted); font-size: 1.0625rem; line-height: 1.55; }}

/* ---------- Section labels inside cards ---------- */
[data-testid="stMarkdownContainer"] p.cx-section {{
  font-weight: 600; font-size: 1rem; color: var(--cx-ink); margin: 0 0 .25rem;
}}
[data-testid="stMarkdownContainer"] p.cx-hint {{
  font-size: .875rem; line-height: 1.5; color: var(--cx-muted); margin: 0 0 .75rem;
}}

/* ---------- Bottom action bar ---------- */
.st-key-cx-actions {{
  margin-top: 1.5rem; padding-top: 1.25rem; border-top: 1px solid var(--cx-line);
}}
.cx-status {{ font-size: .875rem; font-weight: 500; }}
.cx-status.is-saved {{ color: var(--cx-done); }}
.cx-status.is-dirty {{ color: var(--cx-warn); }}

/* ---------- Connection details ---------- */
.cx-conn {{
  display: grid; grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: .875rem 1.5rem; margin: .5rem 0 1rem;
}}
.cx-conn dt {{ font-size: .8125rem; color: var(--cx-muted); margin: 0; }}
.cx-conn dd {{ margin: .125rem 0 0; font-weight: 500; color: var(--cx-ink); overflow-wrap: anywhere; }}

/* ---------- Sync tracker ---------- */
.cx-track {{ list-style: none; margin: .25rem 0 0; padding: 0; }}
.cx-track li {{
  position: relative; display: flex; gap: .875rem; padding: 0 0 1.125rem;
}}
.cx-track li:not(:last-child)::before {{
  content: ""; position: absolute; left: .6875rem; top: 1.625rem; bottom: .125rem;
  width: 2px; background: var(--cx-line);
}}
.cx-track li.is-done:not(:last-child)::before {{ background: var(--cx-done); }}
.cx-ti {{
  flex: none; width: 1.375rem; height: 1.375rem; margin-top: .0625rem;
  border-radius: 50%; border: 2px solid var(--cx-line); background: #fff;
  display: grid; place-items: center; font-size: .75rem; font-weight: 700;
  color: #fff; box-sizing: border-box;
}}
.cx-track li.is-done .cx-ti {{ background: var(--cx-done); border-color: var(--cx-done); }}
.cx-track li.is-done .cx-ti::after {{ content: "✓"; }}
.cx-track li.is-error .cx-ti {{ background: #B42318; border-color: #B42318; }}
.cx-track li.is-error .cx-ti::after {{ content: "✕"; }}
.cx-track li.is-waiting .cx-ti {{ border-color: var(--cx-warn); }}
.cx-track li.is-waiting .cx-ti::after {{ content: ""; width: .375rem; height: .375rem; border-radius: 50%; background: var(--cx-warn); }}
.cx-track li.is-active .cx-ti {{
  border-color: var(--cx-line); border-top-color: var(--cx-primary);
  animation: cx-spin .9s linear infinite;
}}
@keyframes cx-spin {{ to {{ transform: rotate(360deg); }} }}
.cx-track .cx-tt {{ font-weight: 600; color: var(--cx-ink); font-size: .9375rem; line-height: 1.5rem; }}
.cx-track li.is-pending .cx-tt {{ color: var(--cx-muted); }}
.cx-track .cx-td {{ font-size: .875rem; color: var(--cx-muted); line-height: 1.45; }}
.cx-track .cx-td a {{ color: var(--cx-primary); font-weight: 500; white-space: nowrap; }}
.cx-track li.is-error .cx-td {{ color: #B42318; }}

/* ---------- Snap Analytics mark, bottom-right corner ---------- */
.cx-corner {{
  position: fixed; z-index: 999990; pointer-events: none;
  left: 1.25rem; bottom: calc(1rem + env(safe-area-inset-bottom, 0px));
  display: flex; align-items: center;
  padding: .3rem .5rem; border-radius: .375rem;
  background: rgba(255, 255, 255, .94);
}}
.cx-corner img {{ height: 18px; width: auto; display: block; }}
.cx-corner span {{ font-size: .75rem; font-weight: 600; color: var(--cx-muted); }}

/* ---------- Quieter defaults ---------- */
[data-testid="stExpander"] summary p {{ font-weight: 500; }}

/* ---------- Small screens ---------- */
@media (max-width: 760px) {{
  .block-container {{ padding-top: 3.5rem; }}
  .cx-brand .cx-divider, .cx-brand .cx-product {{ display: none; }}
  .cx-brand img {{ height: 40px; }}
  .cx-step-status {{ display: none; }}
  [class*="st-key-cx-step-"] [data-testid="stPageLink"] p {{ font-size: .8125rem; }}
  .cx-conn {{ grid-template-columns: minmax(0, 1fr); }}
  .cx-corner img {{ height: 14px; }}
}}

@media (prefers-reduced-motion: reduce) {{
  * {{ transition: none !important; animation: none !important; }}
}}
</style>
"""


def apply_branding():
    """Call once per run, from app.py, before the page runs."""
    st.markdown(_css(), unsafe_allow_html=True)

    snap = snap_logo_path()
    mark = _img_tag(snap, COMPANY) if snap else f"<span>{html.escape(COMPANY)}</span>"
    st.markdown(
        f'<div class="cx-corner" aria-label="{html.escape(COMPANY)}">{mark}</div>',
        unsafe_allow_html=True,
    )


##################################################
# HEADER
##################################################

def brand_block(show_logo=False):
    """Project name on the left; connection and file status on the right."""
    logo = compass_logo_path() if show_logo else None
    mark = _img_tag(logo, PROJECT) if logo else ""

    conn = st.session_state.get("connection_info")
    if st.session_state.get("snowflake") and conn:
        conn_pill = (
            '<span class="cx-pill is-ok"><span class="cx-dot"></span>'
            f'Snowflake <b>{html.escape(conn["account"])}</b></span>'
            f'<span class="cx-pill">User <b>{html.escape(conn["username"])}</b></span>'
        )
    else:
        conn_pill = '<span class="cx-pill"><span class="cx-dot"></span>Not connected</span>'

    src = st.session_state.saved["model"].get("source_file")
    file_pill = (
        f'<span class="cx-pill">File <b>{html.escape(src)}</b></span>' if src else ""
    )

    st.markdown(
        f'<div class="cx-header">'
        f'<div class="cx-brand">{mark}'
        f'<span class="cx-wordmark">{html.escape(PROJECT)}</span>'
        f'<span class="cx-divider" aria-hidden="true"></span>'
        f'<span class="cx-product">{html.escape(PRODUCT)}</span></div>'
        f'<div class="cx-pills">{conn_pill}{file_pill}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def page_header(title, description=None):
    desc = f"<p>{html.escape(description)}</p>" if description else ""
    st.markdown(
        f'<div class="cx-title"><h1>{html.escape(title)}</h1>{desc}</div>',
        unsafe_allow_html=True,
    )


##################################################
# STEP NAVIGATION
##################################################

def _plural(n, word):
    return f"{n} {word}{'' if n == 1 else 's'}"


def _step_states():
    """(done, warn, status text) for each step, from what is saved."""
    saved = st.session_state.saved
    n_ds = len(saved["datasets"]["tables"])
    n_rel = len(saved["relationships"])
    n_met = len(saved["metrics"])

    states = {
        "connect": (
            bool(st.session_state.snowflake), False,
            "Connected" if st.session_state.snowflake else "Not connected",
        ),
        "datasets": (
            n_ds > 0, False,
            _plural(n_ds, "dataset") if n_ds else "Nothing saved yet",
        ),
        "relationships": (
            n_rel > 0, False,
            _plural(n_rel, "join") if n_rel else "Optional",
        ),
        "metrics": (
            n_met > 0, False,
            _plural(n_met, "metric") if n_met else "Optional",
        ),
    }

    if n_ds:
        errors, _ = validate(saved)
        states["publish"] = (
            not errors, bool(errors),
            _plural(len(errors), "issue") + " to fix" if errors else "Ready",
        )
    else:
        states["publish"] = (False, False, "Needs datasets")

    return states


def progress_rail(current_title):
    """The steps as clickable links, with each step's saved status under it."""
    states = _step_states()

    with st.container(key="cx-rail"):
        cols = st.columns(len(PAGES))
        for i, (col, page) in enumerate(zip(cols, PAGES), start=1):
            done, warn, status = states[page["key"]]
            current = page["title"] == current_title
            flags = "".join([
                "-current" if current else "",
                "-warn" if warn else ("-done" if done else ""),
            ])
            icon = (
                ":material/error:" if warn
                else ":material/check_circle:" if done
                else f":material/counter_{i}:"
            )
            with col:
                with st.container(key=f"cx-step-{page['key']}{flags}"):
                    st.page_link(page["path"], label=page["title"], icon=icon)
                    st.markdown(
                        f'<div class="cx-step-status">{html.escape(status)}</div>',
                        unsafe_allow_html=True,
                    )


##################################################
# ACTIONS
##################################################

def go_back(key, label=None, full_width=True):
    page = BY_KEY[key]
    if st.button(
        label or f"Back to {page['title']}",
        key=f"back_{key}",
        icon=":material/arrow_back:",
        width="stretch" if full_width else "content",
    ):
        st.switch_page(page["path"])


def nav_bar(back=None, forward=None):
    """Bottom bar for pages without a Save button: Back left, Continue right."""
    with st.container(key="cx-actions"):
        left, _, right = st.columns([1.35, 2.9, 1.45], vertical_alignment="center")
        if back:
            with left:
                go_back(back)
        if forward:
            with right:
                continue_to(*forward)


def continue_to(key, label=None, primary=False, full_width=True):
    page = BY_KEY[key]
    if st.button(
        label or f"Continue to {page['title']}",
        key=f"continue_{key}_{label or page['title']}",
        type="primary" if primary else "secondary",
        icon=":material/arrow_forward:",
        width="stretch" if full_width else "content",
    ):
        st.switch_page(page["path"])
