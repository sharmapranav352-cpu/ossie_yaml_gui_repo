import html

import streamlit as st

from services.snowflake_service import SnowflakeService
from utils.branding import continue_to, page_header
from utils.state import init_state

AUTH_METHODS = {
    "Programmatic access token": {
        "authenticator": "snowflake",
        "help": (
            "Generate one in Snowsight under Authentication, then "
            "Programmatic access tokens. Best choice if your only MFA method "
            "is a passkey. If Snowsight shows a missing network policy "
            "warning, ask an admin to add one or the connection will fail "
            "with a 401."
        ),
    },
    "Duo push": {
        "authenticator": "snowflake",
        "help": (
            "Select Connect, then approve the Duo notification on your phone. "
            "Only works if Duo is registered as an MFA method on your account."
        ),
    },
    "Authenticator passcode": {
        "authenticator": "username_password_mfa",
        "help": (
            "Enter the current 6-digit code from your authenticator app. "
            "Only works if a TOTP authenticator is registered on your account."
        ),
    },
    "Browser single sign-on": {
        "authenticator": "externalbrowser",
        "help": (
            "Opens a browser on the machine running this app to complete SSO. "
            "Won't work on a headless server such as EC2."
        ),
    },
    "Password only": {
        "authenticator": "snowflake",
        "help": "For accounts without MFA.",
    },
}

init_state()

page_header(
    "Build a Snowflake semantic model",
    "Pick the tables your analysts use, describe how they join, define "
    "the business metrics, and export an OSSIE YAML file ready to deploy.",
)

##################################################
# CONNECTED
##################################################

conn = st.session_state.get("connection_info")

if st.session_state.snowflake and conn:

    with st.container(border=True):

        st.markdown("**Connected to Snowflake**")

        fields = [
            ("Account", conn["account"]),
            ("User", conn["username"]),
            ("Role", conn["role"] or "Default"),
            ("Warehouse", conn["warehouse"] or "Default"),
        ]
        st.markdown(
            '<dl class="ossie-conn">' + "".join(
                f"<div><dt>{k}</dt><dd>{html.escape(str(v))}</dd></div>"
                for k, v in fields
            ) + "</dl>",
            unsafe_allow_html=True,
        )

        c1, c2, _ = st.columns([1.4, 1, 2.6])
        with c1:
            continue_to("datasets", "Continue to datasets", primary=True)
        with c2:
            if st.button("Disconnect", use_container_width=True):
                try:
                    st.session_state.snowflake.conn.close()
                except Exception:
                    pass
                st.session_state.snowflake = None
                st.session_state.connection_info = None
                st.session_state.meta_cache = {}
                st.rerun()

    st.stop()

##################################################
# CONNECTION FORM
##################################################

with st.container(border=True):

    st.subheader("Connect to Snowflake")

    col1, col2 = st.columns(2)

    with col1:
        account = st.text_input(
            "Account identifier",
            placeholder="orgname-accountname",
            help="Found in Snowsight under your account menu.",
        )
        username = st.text_input("Username")

    with col2:
        warehouse = st.text_input("Warehouse", placeholder="Optional")
        role = st.text_input("Role", placeholder="Optional")

    method = st.selectbox("Sign-in method", list(AUTH_METHODS))
    auth = AUTH_METHODS[method]
    st.caption(auth["help"])

    password = None
    passcode = None
    pat = None

    if method == "Programmatic access token":
        pat = st.text_input("Access token", type="password")
    elif method == "Browser single sign-on":
        pass
    else:
        password = st.text_input("Password", type="password")
        if method == "Authenticator passcode":
            passcode = st.text_input("6-digit passcode", max_chars=6)

    missing = not account.strip() or not username.strip()

    if st.button(
        "Connect",
        type="primary",
        disabled=missing,
        help="Enter an account and username first." if missing else None,
    ):
        with st.spinner("Connecting to Snowflake..."):
            try:
                sf = SnowflakeService(
                    account=account.strip(),
                    username=username.strip(),
                    password=password,
                    warehouse=warehouse.strip() or None,
                    role=role.strip() or None,
                    authenticator=auth["authenticator"],
                    passcode=passcode,
                    pat=pat,
                )
            except Exception as e:
                st.error(f"Couldn't connect. Snowflake said: {e}")
            else:
                st.session_state.snowflake = sf
                st.session_state.connection_info = {
                    "account": account.strip(),
                    "username": username.strip(),
                    "role": role.strip(),
                    "warehouse": warehouse.strip(),
                    "method": method,
                }
                st.session_state.meta_cache = {}
                st.rerun()

saved = st.session_state.saved
if saved["datasets"]["tables"]:
    st.caption(
        "Your last saved model is still here. You can review relationships, "
        "metrics and the YAML without connecting; editing datasets needs a "
        "connection."
    )
