import html

import streamlit as st

from services.ossie_import import OssieImportError, parse_ossie_yaml
from services.snowflake_service import SnowflakeService
from utils.branding import continue_to, page_header, section_heading
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
# MODEL CARD: open an existing file or start fresh
##################################################

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


def model_card():
    saved = st.session_state.saved
    current = source_file()

    with st.container(border=True):

        st.markdown('<p class="cx-section">Model</p>', unsafe_allow_html=True)

        if current:
            n_ds = len(saved["datasets"]["tables"])
            n_rel = len(saved["relationships"])
            n_met = len(saved["metrics"])
            st.markdown(
                f'<p class="cx-hint">Editing <b>{html.escape(current)}</b>: '
                f'{n_ds} dataset{"" if n_ds == 1 else "s"}, '
                f'{n_rel} relationship{"" if n_rel == 1 else "s"}, '
                f'{n_met} metric{"" if n_met == 1 else "s"}.</p>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<p class="cx-hint">Open an Ossie YAML file to edit it, or '
                'start a new model on the Datasets page.</p>',
                unsafe_allow_html=True,
            )

        files = [f.name for f in list_yamls()]
        if files:
            c1, c2 = st.columns([3, 1.1], vertical_alignment="bottom")
            choice = c1.selectbox(
                "File",
                files,
                index=files.index(current) if current in files else 0,
                key="open_repo_choice",
            )
            label = "Reload" if choice == current else "Open"
            if c2.button(label, key="open_repo_btn", width="stretch",
                         help="Load this file, replacing any unsaved edits."):
                _open(read_yaml(choice), choice)

        with st.expander("Upload a file instead"):
            upload = st.file_uploader(
                "Ossie YAML file", type=["yaml", "yml"], key="open_upload",
                label_visibility="collapsed",
            )
            if upload is not None and st.button("Open uploaded file", key="open_upload_btn"):
                _open(upload.getvalue().decode("utf-8"), upload.name)

        notes = st.session_state.get("import_notes")
        if notes:
            with st.expander(f"{len(notes)} note(s) from opening the file", expanded=True):
                for n in notes:
                    st.markdown(f"- {n}")

        if current or saved["datasets"]["tables"]:
            if st.button("Start a new model", icon=":material/add:",
                         key="new_model_btn"):
                reset_config()
                st.session_state.pop("import_notes", None)
                st.rerun()


##################################################
# PAGE
##################################################

init_state()

page_header(
    "Build a semantic model",
    "Pick the tables your analysts use, describe how they join, define "
    "the business metrics, and publish an Ossie YAML file ready to deploy.",
    compact=True,
)

left, right = st.columns([1.45, 1], gap="medium")

conn = st.session_state.get("connection_info")

with left:

    section_heading(
        "Create a New Semantic Model",
        "Connect to Snowflake, then choose the tables, joins and metrics to "
        "build a semantic model from scratch.",
    )

    ##################################################
    # CONNECTED
    ##################################################

    if st.session_state.snowflake and conn:

        with st.container(border=True):

            st.markdown(
                '<p class="cx-section">Snowflake</p>'
                '<p class="cx-hint" style="color:#217A4F">Connected</p>',
                unsafe_allow_html=True,
            )

            fields = [
                ("Account", conn["account"]),
                ("User", conn["username"]),
                ("Role", conn["role"] or "Default"),
                ("Warehouse", conn["warehouse"] or "Default"),
            ]
            st.markdown(
                '<dl class="cx-conn">' + "".join(
                    f"<div><dt>{k}</dt><dd>{html.escape(str(v))}</dd></div>"
                    for k, v in fields
                ) + "</dl>",
                unsafe_allow_html=True,
            )

            c1, c2 = st.columns([1.5, 1])
            with c1:
                continue_to("datasets", "Continue to datasets", primary=True)
            with c2:
                if st.button("Disconnect", width="stretch"):
                    try:
                        st.session_state.snowflake.conn.close()
                    except Exception:
                        pass
                    st.session_state.snowflake = None
                    st.session_state.connection_info = None
                    st.session_state.meta_cache = {}
                    st.rerun()

    ##################################################
    # CONNECTION FORM
    ##################################################

    else:

        with st.container(border=True):

            st.markdown(
                '<p class="cx-section">Connect to Snowflake</p>',
                unsafe_allow_html=True,
            )

            col1, col2 = st.columns(2)
            account = col1.text_input(
                "Account identifier",
                placeholder="orgname-accountname",
                help="Found in Snowsight under your account menu.",
            )
            username = col2.text_input("Username")
            warehouse = col1.text_input("Warehouse", placeholder="Optional")
            role = col2.text_input("Role", placeholder="Optional")

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
                icon=":material/login:",
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

with right:
    section_heading(
        "Update Existing Semantic Model",
        "Open the published model, change it on the next steps, and publish "
        "the update to Snowflake's Semantic Layer.",
    )
    model_card()
    if not st.session_state.snowflake and st.session_state.saved["datasets"]["tables"]:
        st.caption(
            "You can edit relationships and metrics and publish without "
            "connecting. Changing datasets needs a connection."
        )
