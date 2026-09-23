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

st.subheader("Multi-Factor Authentication")

mfa_choice = st.radio(
    "MFA method",
    [
        "Duo Push (approve on phone, no code needed)",
        "Passcode (TOTP from authenticator app)",
        "External Browser / SSO",
        "None"
    ],
    index=0
)

passcode = None
authenticator = "snowflake"

if mfa_choice.startswith("Duo Push"):
    authenticator = "snowflake"
    st.caption(
        "Click Connect, then approve the Duo push notification sent to "
        "your phone. The app will wait until you approve or it times out."
    )

elif mfa_choice.startswith("Passcode"):
    authenticator = "username_password_mfa"
    passcode = st.text_input(
        "6-digit passcode",
        max_chars=6
    )
    st.caption(
        "Enter the current code from your authenticator app (e.g. Duo "
        "Mobile, Google Authenticator) alongside your password."
    )

elif mfa_choice.startswith("External Browser"):
    authenticator = "externalbrowser"
    st.caption(
        "A browser window will open on the machine running this app for "
        "you to complete SSO login. This only works if that machine has "
        "a browser available -- it will not work on a headless server."
    )

else:
    authenticator = "snowflake"

if st.button("Connect"):

    try:

        sf = SnowflakeService(
            account=account,
            username=username,
            password=password,
            warehouse=warehouse,
            role=role,
            authenticator=authenticator,
            passcode=passcode
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