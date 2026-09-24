"""
Look and feel for the app: logo, styling, progress bar and page headers.

Colours come from .streamlit/config.toml, so the brand colour is set in one
place. The logo is read from the assets/ folder (see assets/README.md).
"""

import html
from pathlib import Path

import streamlit as st

from services.builders import validate
from utils.navigation import BY_KEY, PAGES

COMPANY = "Snap Analytics"
PRODUCT = "Semantic Model Builder"

ASSETS = Path("assets")


##################################################
# LOGO
##################################################

def _first_existing(*names):
    for name in names:
        path = ASSETS / name
        if path.exists():
            return str(path)
    return None


def logo_path():
    return _first_existing("snap_logo.svg", "snap_logo.png", "snap_logo.jpg")


def icon_path():
    return _first_existing("snap_icon.png", "snap_icon.svg") or logo_path()


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
  --ossie-primary: {primary};
  --ossie-ink: {ink};
  --ossie-line: {line};
  --ossie-surface: {surface};
  --ossie-muted: #5A6878;
  --ossie-done: #217A4F;
}}

/* Page frame */
.block-container {{
  max-width: 1120px;
  padding-top: 4.5rem;
  padding-bottom: 4rem;
}}
[data-testid="stDecoration"], footer {{ display: none; }}

h1 {{ letter-spacing: -0.015em; }}
h2, h3 {{ letter-spacing: -0.005em; }}

/* Page header */
.ossie-header {{ margin: 0 0 1.5rem; max-width: 46rem; }}
.ossie-header h1 {{ margin: 0 0 .375rem; padding: 0; line-height: 1.2; }}
.ossie-header p {{
  margin: 0; color: var(--ossie-muted);
  font-size: 1.0625rem; line-height: 1.55;
}}

/* Front-page brand block */
.ossie-brand {{
  display: flex; align-items: center; gap: .75rem;
  color: var(--ossie-muted); font-size: .9375rem; font-weight: 500;
  margin-bottom: 1.5rem;
}}
.ossie-brand img {{ height: 44px; width: auto; display: block; }}
.ossie-brand .ossie-wordmark {{
  color: var(--ossie-ink); font-weight: 700; font-size: 1.375rem;
  letter-spacing: -0.02em;
}}
.ossie-brand .ossie-divider {{
  width: 1px; height: 28px; background: var(--ossie-line);
}}

/* Progress bar: the one signature element */
.ossie-rail {{
  list-style: none; display: flex; margin: 0 0 2.25rem; padding: 0;
  border-bottom: 1px solid var(--ossie-line);
}}
.ossie-rail li {{
  flex: 1 1 0; display: flex; gap: .625rem; align-items: flex-start;
  padding: .25rem .75rem .875rem 0; margin-bottom: -1px;
  border-bottom: 3px solid transparent; min-width: 0;
}}
.ossie-rail .ossie-num {{
  flex: none; width: 1.625rem; height: 1.625rem; border-radius: 50%;
  display: grid; place-items: center;
  font-size: .8125rem; font-weight: 600;
  border: 1.5px solid var(--ossie-line); color: var(--ossie-muted);
  background: #fff;
}}
.ossie-rail .ossie-text {{ display: flex; flex-direction: column; min-width: 0; }}
.ossie-rail .ossie-label {{
  font-weight: 600; font-size: .9375rem; color: var(--ossie-ink);
  line-height: 1.625rem; white-space: nowrap;
}}
.ossie-rail .ossie-status {{
  font-size: .8125rem; color: var(--ossie-muted); line-height: 1.3;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}}
.ossie-rail li.is-done .ossie-num {{
  background: var(--ossie-done); border-color: var(--ossie-done); color: #fff;
}}
.ossie-rail li.is-warn .ossie-status {{ color: #9A5B00; }}
.ossie-rail li.is-current {{ border-bottom-color: var(--ossie-primary); }}
.ossie-rail li.is-current .ossie-num {{
  border-color: var(--ossie-primary); color: var(--ossie-primary);
}}
.ossie-rail li.is-current.is-done .ossie-num {{
  background: var(--ossie-primary); color: #fff;
}}
@media (max-width: 760px) {{
  .block-container {{ padding-top: 4.5rem; }}
  .ossie-rail li {{ flex: 0 0 auto; padding-right: .5rem; gap: .375rem; }}
  .ossie-rail li:not(.is-current) .ossie-text {{ display: none; }}
  .ossie-rail li.is-current {{ flex: 1 1 auto; }}
}}

/* Connection status panel */
.ossie-conn {{
  display: grid; grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 1rem 1.5rem; margin: .25rem 0 .5rem;
}}
.ossie-conn dt {{ font-size: .8125rem; color: var(--ossie-muted); margin: 0; }}
.ossie-conn dd {{
  margin: .125rem 0 0; font-weight: 500; color: var(--ossie-ink);
  overflow-wrap: anywhere;
}}
@media (max-width: 760px) {{
  .ossie-conn {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
}}

/* Quieter expanders and code */
[data-testid="stExpander"] summary p {{ font-weight: 500; }}

@media (prefers-reduced-motion: reduce) {{
  * {{ transition: none !important; animation: none !important; }}
}}
</style>
"""


def apply_branding():
    """Call once per run, from app.py, before the page runs."""
    st.markdown(_css(), unsafe_allow_html=True)

    logo = logo_path()
    if logo:
        st.logo(logo, size="large", icon_image=icon_path())


##################################################
# HEADERS
##################################################

def _img_tag(path, alt):
    import base64
    import mimetypes

    mime = mimetypes.guess_type(path)[0] or "image/png"
    if path.endswith(".svg"):
        mime = "image/svg+xml"
    data = base64.b64encode(Path(path).read_bytes()).decode()
    return f'<img src="data:{mime};base64,{data}" alt="{html.escape(alt)}">'


def brand_block():
    """Logo (or company name) and product name, for the front page."""
    logo = logo_path()
    mark = (
        _img_tag(logo, COMPANY)
        if logo
        else f'<span class="ossie-wordmark">{html.escape(COMPANY)}</span>'
    )
    st.markdown(
        f'<div class="ossie-brand">{mark}'
        f'<span class="ossie-divider" aria-hidden="true"></span>'
        f'<span>{html.escape(PRODUCT)}</span></div>',
        unsafe_allow_html=True,
    )


def page_header(title, description=None):
    desc = f"<p>{html.escape(description)}</p>" if description else ""
    st.markdown(
        f'<div class="ossie-header"><h1>{html.escape(title)}</h1>{desc}</div>',
        unsafe_allow_html=True,
    )


##################################################
# PROGRESS BAR
##################################################

def _plural(n, word):
    return f"{n} {word}{'' if n == 1 else 's'}"


def _step_states():
    """(done, warn, status text) for each step, from what is saved."""
    saved = st.session_state.saved
    conn = st.session_state.get("connection_info")

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
            _plural(n_ds, "dataset") + " saved" if n_ds else "Nothing saved yet",
        ),
        "relationships": (
            n_rel > 0, False,
            _plural(n_rel, "join") + " saved" if n_rel else "Optional",
        ),
        "metrics": (
            n_met > 0, False,
            _plural(n_met, "metric") + " saved" if n_met else "Optional",
        ),
    }

    if n_ds:
        errors, _ = validate(saved)
        states["generate"] = (
            not errors, bool(errors),
            _plural(len(errors), "issue") + " to fix" if errors else "Ready",
        )
    else:
        states["generate"] = (False, False, "Needs datasets")

    return states


def progress_rail(current_title):
    states = _step_states()
    items = []

    for i, page in enumerate(PAGES, start=1):
        done, warn, status = states[page["key"]]
        current = page["title"] == current_title

        classes = " ".join(
            c for c, on in (
                ("is-done", done), ("is-warn", warn), ("is-current", current)
            ) if on
        )
        num = "&#10003;" if done else str(i)
        aria = ' aria-current="step"' if current else ""

        items.append(
            f'<li class="{classes}"{aria}>'
            f'<span class="ossie-num" aria-hidden="true">{num}</span>'
            f'<span class="ossie-text">'
            f'<span class="ossie-label">{html.escape(page["title"])}</span>'
            f'<span class="ossie-status">{html.escape(status)}</span>'
            f"</span></li>"
        )

    st.markdown(
        '<ol class="ossie-rail" aria-label="Progress">' + "".join(items) + "</ol>",
        unsafe_allow_html=True,
    )


##################################################
# NEXT STEP
##################################################

def continue_to(key, label=None, primary=False):
    page = BY_KEY[key]
    if st.button(
        label or f"Continue to {page['title']}",
        key=f"continue_{key}_{label or page['title']}",
        type="primary" if primary else "secondary",
        icon=":material/arrow_forward:",
    ):
        st.switch_page(page["path"])
