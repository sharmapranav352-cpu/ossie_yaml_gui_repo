import streamlit as st
from services.snowflake_service import SnowflakeService

st.set_page_config(
    page_title="OSSIE Generator",
    layout="wide"
)

st.title("OSSIE YAML Generator")

if "snowflake" not in st.session_state:
    st.session_state.snowflake = None

if "datasets" not in st.session_state:
    st.session_state.datasets = []

if "relationships" not in st.session_state:
    st.session_state.relationships = []

if "metrics" not in st.session_state:
    st.session_state.metrics = []

st.header("Snowflake Connection")

col1, col2 = st.columns(2)

with col1:

    account = st.text_input(
        "Account"
    )

    username = st.text_input(
        "Username"
    )

    password = st.text_input(
        "Password",
        type="password"
    )

with col2:

    warehouse = st.text_input(
        "Warehouse"
    )

    role = st.text_input(
        "Role"
    )

if st.button("Connect"):

    try:

        sf = SnowflakeService(
            account=account,
            username=username,
            password=password,
            warehouse=warehouse,
            role=role
        )

        st.session_state.snowflake = sf

        st.success(
            "Connected Successfully"
        )

    except Exception as e:

        st.error(str(e))

if st.session_state.snowflake:

    st.success(
        "Snowflake Session Active"
    )

    st.info(
        "Use left navigation to continue."
    )