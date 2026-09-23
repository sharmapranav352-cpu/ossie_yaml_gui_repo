import json
import re

import streamlit as st

from services.builders import (
    build_datasets,
    build_metrics,
    build_relationships,
    validate,
)
from services.yaml_service import OssieGenerator
from utils.file_manager import list_yamls, save_yaml
from utils.state import (
    config_json,
    init_state,
    replace_config,
    reset_config,
    save_section,
    seed_value,
)

st.title("Generate OSSIE YAML")

init_state()

saved = st.session_state.saved

#################################################
# MODEL DETAILS
#################################################

seed_value("gen_model_name", saved["model"]["name"])
seed_value("gen_model_desc", saved["model"]["description"])

model_name = st.text_input("Semantic Model Name", key="gen_model_name")
model_description = st.text_area("Description", key="gen_model_desc")

model_cfg = {
    "name": model_name.strip(),
    "description": model_description.strip(),
}

if model_cfg != saved["model"]:
    save_section("model", model_cfg)

#################################################
# SUMMARY (SAVED CONFIG ONLY)
#################################################

st.caption(
    "The YAML is generated from what you saved on each page. "
    "Unsaved edits on other pages are not included."
)

col1, col2, col3 = st.columns(3)
col1.metric("Saved Datasets", len(saved["datasets"]["tables"]))
col2.metric("Saved Relationships", len(saved["relationships"]))
col3.metric("Saved Metrics", len(saved["metrics"]))

#################################################
# VALIDATION
#################################################

errors, warnings = validate(saved)

for e in errors:
    st.error(e)

if warnings:
    with st.expander(f"{len(warnings)} warning(s)"):
        for w in warnings:
            st.warning(w)

#################################################
# YAML GENERATION
#################################################

if st.button(
    "Generate YAML",
    type="primary",
    disabled=bool(errors)
):
    st.session_state.generated_yaml = OssieGenerator.generate(
        model_name=model_cfg["name"],
        description=model_cfg["description"],
        datasets=build_datasets(saved["datasets"]),
        relationships=build_relationships(saved["relationships"]),
        metrics=build_metrics(saved["metrics"]),
    )
    st.session_state.generated_for = model_cfg["name"]

if "generated_yaml" in st.session_state:

    st.subheader("Generated YAML")

    st.code(st.session_state.generated_yaml, language="yaml")

    safe_name = re.sub(
        r"[^A-Za-z0-9_.-]", "_",
        st.session_state.get("generated_for") or "model"
    )
    filename = f"{safe_name}.yaml"

    c1, c2 = st.columns(2)

    with c1:
        if st.button("Save YAML"):
            save_yaml(filename, st.session_state.generated_yaml)
            st.success(f"Saved outputs/{filename}")

    with c2:
        st.download_button(
            label="Download YAML",
            data=st.session_state.generated_yaml,
            file_name=filename,
            mime="text/yaml"
        )

#################################################
# SAVED FILES
#################################################

st.divider()
st.subheader("Saved YAML Files")

files = list_yamls()

if files:
    for file in files:
        st.write(file.name)
else:
    st.info("No saved YAMLs")

#################################################
# PROJECT CONFIGURATION
#################################################

st.divider()
st.subheader("Project Configuration")

st.caption(
    "Your saved settings are stored in saved_config/model_config.json "
    "and reloaded automatically. You can also export them or load a "
    "previous project."
)

st.download_button(
    "⬇ Export configuration (JSON)",
    data=config_json(),
    file_name=f"{model_cfg['name'] or 'model'}_config.json",
    mime="application/json"
)

uploaded = st.file_uploader("Load a configuration file", type=["json"])

if uploaded is not None and st.button("Load this configuration"):
    try:
        replace_config(json.loads(uploaded.getvalue().decode("utf-8")))
        st.session_state.pop("generated_yaml", None)
        st.rerun()
    except ValueError as exc:
        st.error(f"Could not read that file: {exc}")

with st.expander("Reset everything"):
    confirm = st.checkbox("I want to clear all saved datasets, relationships and metrics")
    if st.button("Reset", disabled=not confirm):
        reset_config()
        st.session_state.pop("generated_yaml", None)
        st.rerun()
