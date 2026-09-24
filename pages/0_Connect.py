import html

import streamlit as st

from services.ossie_import import OssieImportError, parse_ossie_yaml
from services.snowflake_service import SnowflakeService
from utils.branding import continue_to, page_header
from utils.file_manager import list_yamls, read_yaml
from utils.state import init_state, open_config, reset_config, source_file

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


##################################################
# OPEN AN EXISTING MODEL
##################################################

def open_model_section():

    st.write("")

    with st.container(border=True):

        current = source_file()
        has_work = bool(st.session_state.saved["datasets"]["tables"])

        st.subheader("Start from an existing model")

        if current:
            st.markdown(
                f"You're editing **outputs/{current}**. Change it on the "
                "Datasets, Relationships and Metrics pages, then update the "
                "file on the Generate YAML page."
            )
        else:
            st.caption(
                "Open an OSSIE YAML file to change it, instead of building a "
                "model from scratch."
            )

        files = [f.name for f in list_yamls()]
        tab_repo, tab_upload = st.tabs(["From the repo", "Upload a file"])

        with tab_repo:
            if files:
                c1, c2 = st.columns([3, 1], vertical_alignment="bottom")
                choice = c1.selectbox(
                    "File in outputs/",
                    files,
                    index=files.index(current) if current in files else 0,
                    key="open_repo_choice",
                )
                if c2.button("Open", key="open_repo_btn", use_container_width=True):
                    _open(read_yaml(choice), choice)
            else:
                st.caption("No YAML files in outputs/ yet.")

        with tab_upload:
            upload = st.file_uploader(
                "OSSIE YAML file", type=["yaml", "yml"], key="open_upload"
            )
            if upload is not None and st.button("Open", key="open_upload_btn"):
                _open(upload.getvalue().decode("utf-8"), upload.name)

        if has_work and not current:
            st.caption(
                "Opening a file replaces the model you're working on now."
            )

        notes = st.session_state.get("import_notes")
        if notes:
            with st.expander(f"{len(notes)} note(s) from opening the file", expanded=True):
                for n in notes:
                    st.markdown(f"- {n}")

        if current:
            c1, c2, _ = st.columns([1.4, 1.4, 2.2])
            with c1:
                continue_to("datasets", "Edit datasets", primary=True)
            with c2:
                if st.button("Start a new model", use_container_width=True):
                    reset_config()
                    st.session_state.pop("import_notes", None)
                    st.rerun()


def _open(text, filename):
    if text is None:
        st.error(f"Couldn't read outputs/{filename}.")
        return
    try:
        cfg, notes = parse_ossie_yaml(text)
    except OssieImportError as exc:
        st.error(str(exc))
        return
    open_config(cfg, filename)
    st.session_state.import_notes = notes
    st.toast(f"Opened {filename}")
    st.rerun()


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

    open_model_section()
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

open_model_section()

if st.session_state.saved["datasets"]["tables"]:
    st.caption(
        "Your saved model is still here. You can edit relationships, metrics "
        "and the YAML without connecting; editing datasets needs a connection."
    )
