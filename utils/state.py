"""
Shared state handling for the OSSIE generator.

Every builder page keeps two things apart:

  * widget values  - what is currently on screen (may be unsaved)
  * saved config   - what the user committed with a "Save" button

Only the saved config is used to generate the YAML. It lives in
st.session_state.saved and is also written to saved_config/model_config.json
so it survives page switches, browser refreshes and app restarts.

Streamlit deletes a widget's state when you navigate to another page, so the
seed_* helpers below re-populate widgets from the saved config whenever their
state is missing.
"""

import copy
import json
from pathlib import Path

import streamlit as st

CONFIG_DIR = Path("saved_config")
CONFIG_FILE = CONFIG_DIR / "model_config.json"

WIDGET_PREFIXES = ("ds_", "rel_", "met_", "gen_")

EMPTY_CONFIG = {
    "model": {
        "name": "MY_MODEL",
        "description": "Generated Semantic Model",
    },
    "datasets": {
        "database": None,
        "schema": None,
        "tables": [],
    },
    "relationships": [],
    "metrics": [],
}


##################################################
# LOAD / SAVE
##################################################

def normalize(data):
    """Merge loaded data onto the empty template so missing keys never crash."""
    cfg = copy.deepcopy(EMPTY_CONFIG)

    if not isinstance(data, dict):
        return cfg

    for key, default in cfg.items():
        value = data.get(key)
        if value is None:
            continue
        if isinstance(default, dict) and isinstance(value, dict):
            cfg[key].update(value)
        elif isinstance(default, list) and isinstance(value, list):
            cfg[key] = value

    return cfg


def _load_from_disk():
    if CONFIG_FILE.exists():
        try:
            return normalize(
                json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            )
        except (OSError, ValueError):
            pass
    return copy.deepcopy(EMPTY_CONFIG)


def persist():
    CONFIG_DIR.mkdir(exist_ok=True)
    CONFIG_FILE.write_text(
        json.dumps(st.session_state.saved, indent=2),
        encoding="utf-8",
    )


def init_state():
    """Call at the top of app.py and every page."""
    st.session_state.setdefault("snowflake", None)
    st.session_state.setdefault("meta_cache", {})

    if "saved" not in st.session_state:
        st.session_state.saved = _load_from_disk()


def save_section(section, value):
    st.session_state.saved[section] = copy.deepcopy(value)
    persist()


def replace_config(data):
    """Load a whole configuration (e.g. an uploaded project file)."""
    st.session_state.saved = normalize(data)
    persist()
    clear_widget_state()


def reset_config():
    replace_config(copy.deepcopy(EMPTY_CONFIG))


def clear_widget_state():
    for key in list(st.session_state.keys()):
        if isinstance(key, str) and key.startswith(WIDGET_PREFIXES):
            del st.session_state[key]


def config_json():
    return json.dumps(st.session_state.saved, indent=2)


##################################################
# WIDGET SEEDING
##################################################

def seed_choice(key, options, saved=None):
    """Make sure a selectbox key holds a valid option, preferring the saved one."""
    current = st.session_state.get(key)

    if current in options:
        return

    if saved in options:
        st.session_state[key] = saved
    elif options:
        st.session_state[key] = options[0]
    else:
        st.session_state.pop(key, None)


def seed_multi(key, options, saved=None):
    """Make sure a multiselect key only holds valid options."""
    if key in st.session_state:
        st.session_state[key] = [
            v for v in st.session_state[key] if v in options
        ]
    else:
        st.session_state[key] = [
            v for v in (saved or []) if v in options
        ]


def seed_value(key, saved):
    """Seed a free-form widget (text, number) if it has no state yet."""
    if key not in st.session_state:
        st.session_state[key] = saved


##################################################
# SNOWFLAKE METADATA CACHE
##################################################

def cached_meta(name, fn, *args):
    """Avoid re-querying Snowflake metadata on every rerun."""
    cache = st.session_state.meta_cache
    key = "|".join([name, *map(str, args)])

    if key not in cache:
        cache[key] = fn(*args)

    return cache[key]


def clear_meta_cache():
    st.session_state.meta_cache = {}


##################################################
# UI HELPERS
##################################################

def save_bar(label, current, saved, on_save, next_step=None):
    """Save button, a quiet saved/unsaved status, and an optional next step."""
    from utils.branding import continue_to

    col1, col2, col3 = st.columns([1.1, 2.4, 1.5], vertical_alignment="center")

    with col1:
        clicked = st.button(
            label, type="primary", icon=":material/save:",
            use_container_width=True
        )

    if clicked:
        on_save(current)
        saved = current
        st.toast(f"{label.replace('Save ', '').capitalize()} saved")

    with col2:
        if current != saved:
            st.markdown(":orange[:material/pending: Unsaved changes]")
        elif saved:
            st.markdown(":green[:material/check_circle: All changes saved]")

    if next_step:
        with col3:
            continue_to(*next_step)

    return clicked
