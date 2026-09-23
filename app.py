import streamlit as st
from services.snowflake_service import SnowflakeService
from utils.state import init_state

st.set_page_config(
    page_title="OSSIE Generator",
    layout="wide"
)

st.title("OSSIE YAML Generator")

init_state()

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

saved = st.session_state.saved

if saved["datasets"]["tables"]:

    st.divider()

    st.subheader("Saved Configuration")

    c1, c2, c3 = st.columns(3)
    c1.metric("Datasets", len(saved["datasets"]["tables"]))
    c2.metric("Relationships", len(saved["relationships"]))
    c3.metric("Metrics", len(saved["metrics"]))

    st.caption(
        "Loaded from your last session. Relationships, Metrics and "
        "Generate YAML work without reconnecting; editing datasets "
        "needs a Snowflake connection."
    )
