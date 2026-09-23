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

st.subheader("Multi-Factor Authentication")

mfa_choice = st.radio(
    "MFA / auth method",
    [
        "Programmatic Access Token (PAT)",
        "Duo Push (approve on phone, no code needed)",
        "Passcode (TOTP from authenticator app)",
        "External Browser / SSO",
        "None"
    ],
    index=0
)

passcode = None
pat = None
authenticator = "snowflake"

if mfa_choice.startswith("Programmatic"):
    authenticator = "snowflake"
    pat = st.text_input(
        "Programmatic Access Token",
        type="password",
        help=(
            "Generate this under Snowsight -> Authentication -> "
            "Programmatic access tokens. Use this if your only registered "
            "MFA method is a Passkey -- passkeys can't be automated, but "
            "a PAT sidesteps MFA entirely."
        )
    )
    st.caption(
        "If you see a 'Missing network policy' warning on the token "
        "generation page, ask a Snowflake admin to apply a network policy "
        "or authentication policy before this will work -- otherwise the "
        "connection will fail with a 401."
    )

elif mfa_choice.startswith("Duo Push"):
    authenticator = "snowflake"
    st.caption(
        "Click Connect, then approve the Duo push notification sent to "
        "your phone. Only works if Duo is a registered MFA method on "
        "your account -- it won't trigger for passkey-only accounts."
    )

elif mfa_choice.startswith("Passcode"):
    authenticator = "username_password_mfa"
    passcode = st.text_input(
        "6-digit passcode",
        max_chars=6
    )
    st.caption(
        "Enter the current code from your authenticator app. Only works "
        "if a TOTP authenticator is a registered MFA method on your "
        "account -- it won't work for passkey-only accounts."
    )

elif mfa_choice.startswith("External Browser"):
    authenticator = "externalbrowser"
    st.caption(
        "A browser window will open on the machine running this app for "
        "you to complete SSO/passkey login. This only works if that "
        "machine has a browser available -- it will not work on a "
        "headless server like EC2."
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
            passcode=passcode,
            pat=pat
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
