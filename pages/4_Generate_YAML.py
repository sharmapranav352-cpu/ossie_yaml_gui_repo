import streamlit as st

from services.yaml_service import (
    OssieGenerator
)

from utils.file_manager import (
    save_yaml,
    list_yamls
)

st.title(
    "Generate OSSIE YAML"
)

#################################################
# VALIDATION
#################################################

if not st.session_state.datasets:

    st.warning(
        "Dataset configuration required."
    )

    st.stop()

#################################################
# MODEL DETAILS
#################################################

model_name = st.text_input(
    "Semantic Model Name",
    value="MY_MODEL"
)

model_description = st.text_area(
    "Description",
    value="Generated Semantic Model"
)

#################################################
# SUMMARY
#################################################

col1, col2, col3 = st.columns(3)

with col1:

    st.metric(
        "Datasets",
        len(
            st.session_state.datasets
        )
    )

with col2:

    st.metric(
        "Relationships",
        len(
            st.session_state.relationships
        )
    )

with col3:

    st.metric(
        "Metrics",
        len(
            st.session_state.metrics
        )
    )

#################################################
# YAML GENERATION
#################################################

if st.button(
    "Generate YAML",
    type="primary"
):

    yaml_text = (
        OssieGenerator.generate(
            model_name=model_name,
            description=model_description,
            datasets=st.session_state.datasets,
            relationships=st.session_state.relationships,
            metrics=st.session_state.metrics
        )
    )

    st.session_state.generated_yaml = (
        yaml_text
    )

#################################################
# SHOW YAML
#################################################

if "generated_yaml" in st.session_state:

    st.subheader(
        "Generated YAML"
    )

    st.code(
        st.session_state.generated_yaml,
        language="yaml"
    )

    #################################################
    # SAVE
    #################################################

    if st.button(
        "Save YAML"
    ):

        filename = (
            f"{model_name}.yaml"
        )

        save_yaml(
            filename,
            st.session_state.generated_yaml
        )

        st.success(
            f"Saved {filename}"
        )

    #################################################
    # DOWNLOAD
    #################################################

    st.download_button(
        label="Download YAML",
        data=st.session_state.generated_yaml,
        file_name=f"{model_name}.yaml",
        mime="text/yaml"
    )

#################################################
# SAVED FILES
#################################################

st.divider()

st.subheader(
    "Saved YAML Files"
)

files = list_yamls()

if files:

    for file in files:

        st.write(
            file.name
        )

else:

    st.info(
        "No saved YAMLs"
    )