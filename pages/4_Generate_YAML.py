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
from utils.branding import continue_to, page_header
from utils.file_manager import list_yamls, save_yaml
from utils.state import (
    config_json,
    init_state,
    replace_config,
    reset_config,
    save_section,
    seed_value,
)

init_state()

page_header(
    "Generate the semantic model",
    "Name the model, check it, and export the OSSIE YAML. The file is built "
    "from what you saved on each step."
)

saved = st.session_state.saved

#################################################
# MODEL DETAILS
#################################################

with st.container(border=True):

    seed_value("gen_model_name", saved["model"]["name"])
    seed_value("gen_model_desc", saved["model"]["description"])

    c1, c2 = st.columns([1, 2])
    model_name = c1.text_input("Model name", key="gen_model_name")
    model_description = c2.text_input("Description", key="gen_model_desc")

    model_cfg = {
        "name": model_name.strip(),
        "description": model_description.strip(),
    }

    if model_cfg != saved["model"]:
        save_section("model", model_cfg)

#################################################
# CHECKS
#################################################

errors, warnings = validate(saved)

if errors:
    st.error(
        "Fix these before generating:\n\n"
        + "\n".join(f"- {e}" for e in errors)
    )
    if not saved["datasets"]["tables"]:
        continue_to("datasets", "Go to datasets")
else:
    st.success("Everything checks out. The model is ready to generate.")

if warnings:
    label = "1 suggestion" if len(warnings) == 1 else f"{len(warnings)} suggestions"
    with st.expander(f"{label} to improve the model"):
        for w in warnings:
            st.markdown(f"- {w}")

#################################################
# YAML GENERATION
#################################################

if st.button(
    "Generate YAML",
    type="primary",
    icon=":material/play_arrow:",
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

    safe_name = re.sub(
        r"[^A-Za-z0-9_.-]", "_",
        st.session_state.get("generated_for") or "model"
    )
    filename = f"{safe_name}.yaml"
    yaml_text = st.session_state.generated_yaml

    with st.container(border=True):

        h1, h2, h3 = st.columns([3, 1, 1], vertical_alignment="center")

        h1.markdown(
            f"**{filename}**  \n"
            f"<span style='color:#5A6878;font-size:.875rem'>"
            f"{len(yaml_text.splitlines())} lines</span>",
            unsafe_allow_html=True
        )

        with h2:
            st.download_button(
                "Download",
                data=yaml_text,
                file_name=filename,
                mime="text/yaml",
                icon=":material/download:",
                type="primary",
                use_container_width=True
            )

        with h3:
            if st.button(
                "Save to outputs",
                icon=":material/save:",
                use_container_width=True
            ):
                save_yaml(filename, yaml_text)
                st.toast(f"Saved outputs/{filename}")

        st.code(yaml_text, language="yaml", height=520)

#################################################
# PROJECT FILES
#################################################

st.write("")

with st.expander("Project settings and saved files"):

    st.markdown("**Saved YAML files**")
    files = list_yamls()
    if files:
        for file in files:
            st.markdown(f"- `outputs/{file.name}`")
    else:
        st.caption("No YAML files saved yet.")

    st.divider()

    st.markdown("**Configuration**")
    st.caption(
        "Your saved steps are stored in saved_config/model_config.json and "
        "reload automatically. Export them to share a model or reuse it later."
    )

    st.download_button(
        "Export configuration",
        data=config_json(),
        file_name=f"{model_cfg['name'] or 'model'}_config.json",
        mime="application/json",
        icon=":material/upload_file:"
    )

    uploaded = st.file_uploader("Load a configuration file", type=["json"])

    if uploaded is not None and st.button("Load configuration"):
        try:
            replace_config(json.loads(uploaded.getvalue().decode("utf-8")))
            st.session_state.pop("generated_yaml", None)
            st.rerun()
        except ValueError as exc:
            st.error(f"That file isn't a valid configuration: {exc}")

    st.divider()

    st.markdown("**Start over**")
    confirm = st.checkbox(
        "Clear all saved datasets, relationships and metrics"
    )
    if st.button("Clear everything", disabled=not confirm):
        reset_config()
        st.session_state.pop("generated_yaml", None)
        st.rerun()
