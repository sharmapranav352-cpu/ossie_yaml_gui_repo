import difflib
import hashlib
import html
import json
import time
from datetime import datetime

import streamlit as st

from services import github_service, sync_status
from services.builders import (
    build_datasets,
    build_metrics,
    build_relationships,
    validate,
)
from services.yaml_service import OssieGenerator
from utils.branding import continue_to, nav_bar, page_header
from utils.file_manager import (
    EXPECTED_MODEL_NAME,
    FIXED_OUTPUT_FILE,
    read_yaml,
    save_yaml,
)
from utils.state import (
    config_json,
    init_state,
    replace_config,
    reset_config,
    save_section,
    seed_value,
)

init_state()

saved = st.session_state.saved
gh = github_service.settings()
filename = FIXED_OUTPUT_FILE or f"{saved['model']['name'] or 'model'}.yaml"

page_header(
    "Review and publish",
    f"Check the model, review what changed, and publish {filename}"
    + (" to GitHub." if gh else "."),
)

#################################################
# MODEL DETAILS
#################################################

if EXPECTED_MODEL_NAME and saved["model"]["name"] != EXPECTED_MODEL_NAME:
    # The file is deployed under this name, so keep it fixed
    save_section("model", {**saved["model"], "name": EXPECTED_MODEL_NAME})
    saved = st.session_state.saved

with st.container(border=True):

    c1, c2 = st.columns([1, 2.4])

    if EXPECTED_MODEL_NAME:
        c1.text_input(
            "Model name", value=EXPECTED_MODEL_NAME, disabled=True,
            key="gen_model_name_fixed",
            help=f"Fixed: the file is deployed to Snowflake as the "
                 f"{EXPECTED_MODEL_NAME} semantic view.",
        )
        model_name = EXPECTED_MODEL_NAME
    else:
        seed_value("gen_model_name", saved["model"]["name"])
        model_name = c1.text_input("Model name", key="gen_model_name").strip()

    seed_value("gen_model_desc", saved["model"]["description"])
    model_description = c2.text_input(
        "Description", key="gen_model_desc",
        placeholder="What this model is for",
    ).strip()

    model_cfg = {**saved["model"], "name": model_name, "description": model_description}
    if model_cfg != saved["model"]:
        save_section("model", model_cfg)
        saved = st.session_state.saved

#################################################
# CHECKS
#################################################

errors, warnings = validate(saved)

if errors:
    st.error(
        "Fix these before publishing:\n\n" + "\n".join(f"- {e}" for e in errors)
    )
    if not saved["datasets"]["tables"]:
        continue_to("datasets", "Go to datasets", full_width=False)

if warnings:
    label = "1 suggestion" if len(warnings) == 1 else f"{len(warnings)} suggestions"
    with st.expander(f"{label} to improve the model"):
        for w in warnings:
            st.markdown(f"- {w}")

#################################################
# THE YAML, BUILT FROM WHAT IS SAVED
#################################################

@st.cache_data(ttl=60, show_spinner=False)
def _github_version(name, refresh):
    return github_service.read_file(name)


SYNC_TIMEOUT = 15 * 60   # stop checking automatically after 15 minutes
SYNC_EVERY = 5           # seconds between checks while in progress

OVERALL = {
    "done": ("success", "Both repositories are in sync and both deployments finished."),
    "active": ("info", "In progress. This updates by itself every few seconds."),
    "waiting": ("warning", "Waiting for a pull request to be merged. This updates by itself."),
    "error": ("error", "A step failed. See the step marked in red."),
    "idle": ("info", "This version isn't published yet."),
}


def render_sync_status(gh, yaml_text, yaml_hash):
    """Where this YAML is: ossie_yaml_gui_repo, the sync workflow, ossie-semantic-contracts."""
    track = st.session_state.get("sync_track")
    if track and track.get("for") != yaml_hash:
        track = None   # the model changed since that publish

    st.write("")
    with st.container(border=True):
        h1, h2 = st.columns([4, 1], vertical_alignment="center")
        h1.markdown(
            '<p class="cx-section">Sync status</p>'
            f'<p class="cx-hint" style="margin:0">{html.escape(gh["repo"].split("/")[-1])} '
            f'to {html.escape(gh["contracts_repo"].split("/")[-1])}</p>',
            unsafe_allow_html=True,
        )
        if h2.button("Check now", icon=":material/refresh:", key="sync_check",
                     width="stretch"):
            st.session_state.sync_polling = True
            st.session_state.sync_started = time.time()
            st.session_state.sync_checked = True

        if not (track or st.session_state.get("sync_checked")):
            st.markdown(
                '<p class="cx-hint">Publish to follow the file through both '
                'repositories, or select Check now to see where the current '
                'version is.</p>',
                unsafe_allow_html=True,
            )
            return

        polling = st.session_state.get("sync_polling", False)

        @st.fragment(run_every=SYNC_EVERY if polling else None)
        def _tracker():
            try:
                stages, overall = sync_status.check(gh, yaml_text, track)
            except Exception as exc:
                st.error(f"Couldn't check the sync: {exc}")
                return

            items = []
            for i, s in enumerate(stages, start=1):
                link = (f' <a href="{html.escape(s["url"])}" target="_blank">Open</a>'
                        if s.get("url") else "")
                items.append(
                    f'<li class="is-{s["state"]}"><span class="cx-ti"></span><div>'
                    f'<div class="cx-tt">{html.escape(s["label"])}</div>'
                    f'<div class="cx-td">{html.escape(s["detail"] or "Not started yet.")}{link}</div>'
                    f'</div></li>'
                )
            st.markdown('<ol class="cx-track">' + "".join(items) + "</ol>",
                        unsafe_allow_html=True)

            kind, text = OVERALL[overall]
            getattr(st, kind)(text)
            st.caption(f"Last checked {datetime.now().strftime('%H:%M:%S')}")

            # Stop checking once finished, failed, or after the time limit
            still = overall in ("active", "waiting")
            timed_out = time.time() - st.session_state.get("sync_started", 0) > SYNC_TIMEOUT
            if st.session_state.get("sync_polling") and (not still or timed_out):
                st.session_state.sync_polling = False
                st.rerun()

        _tracker()


yaml_text = None
if not errors:
    yaml_text = OssieGenerator.generate(
        model_name=saved["model"]["name"],
        description=saved["model"]["description"],
        datasets=build_datasets(saved["datasets"]),
        relationships=build_relationships(saved["relationships"]),
        metrics=build_metrics(saved["metrics"]),
    )

if yaml_text is not None:

    yaml_hash = hashlib.sha1(yaml_text.encode()).hexdigest()

    # What we compare against: the file on GitHub, else the local copy
    baseline, baseline_label, gh_read_error = None, f"outputs/{filename}", None
    if gh:
        try:
            baseline = _github_version(filename, st.session_state.get("gh_refresh", 0))
            baseline_label = f"{gh['folder']}/{filename} on {gh['branch']}"
        except Exception as exc:
            gh_read_error = str(exc)
    if baseline is None:
        baseline = read_yaml(filename)
        baseline_label = f"outputs/{filename}"

    unchanged = baseline == yaml_text

    st.write("")
    left, right = st.columns([1.75, 1], gap="large")

    #################################################
    # LEFT: CHANGES AND FULL YAML
    #################################################

    with left:
        tab_changes, tab_yaml = st.tabs(["Changes", "Full YAML"])

        with tab_changes:
            if baseline is None:
                st.info(f"{filename} doesn't exist yet. Publishing creates it.")
            elif unchanged:
                st.success(f"No changes. {baseline_label} already matches this model.")
            else:
                diff = "".join(difflib.unified_diff(
                    baseline.splitlines(keepends=True),
                    yaml_text.splitlines(keepends=True),
                    fromfile=f"{filename} (current)",
                    tofile=f"{filename} (new)",
                ))
                added = sum(1 for l in diff.splitlines()
                            if l.startswith("+") and not l.startswith("+++"))
                removed = sum(1 for l in diff.splitlines()
                              if l.startswith("-") and not l.startswith("---"))
                st.markdown(
                    f'<p class="cx-hint">Compared with {baseline_label}: '
                    f'<b style="color:#217A4F">+{added}</b> '
                    f'<b style="color:#B42318">-{removed}</b> lines</p>',
                    unsafe_allow_html=True,
                )
                n_lines = len(diff.splitlines())
                st.code(diff, language="diff", height=440 if n_lines > 20 else None)
            if gh_read_error:
                st.caption(f"Couldn't read the file from GitHub, so this compares "
                           f"with the local copy. {gh_read_error}")

        with tab_yaml:
            st.markdown(
                f'<p class="cx-hint">{filename}, {len(yaml_text.splitlines())} lines, '
                f'Ossie {yaml_text.split(chr(10), 1)[0].split(": ", 1)[-1]}</p>',
                unsafe_allow_html=True,
            )
            st.code(yaml_text, language="yaml", height=440)

    #################################################
    # RIGHT: PUBLISH
    #################################################

    with right:
        with st.container(border=True):

            st.markdown('<p class="cx-section">Publish</p>', unsafe_allow_html=True)

            if gh:
                st.markdown(
                    f'<p class="cx-hint">Saves <b>{gh["folder"]}/{filename}</b> to '
                    f'<b>{gh["repo"].split("/")[-1]}</b>.</p>',
                    unsafe_allow_html=True,
                )

                modes = {"Pull request": "pull_request", f"Commit to {gh['branch']}": "direct"}
                default = f"Commit to {gh['branch']}" if gh["mode"] == "direct" else "Pull request"
                choice = st.segmented_control(
                    "How to publish", list(modes), default=default,
                    key="gen_gh_mode", label_visibility="collapsed",
                ) or default
                st.caption(
                    "Opens a pull request for review. The change reaches "
                    f"{gh['branch']} when you merge it."
                    if modes[choice] == "pull_request" else
                    f"Saves straight to {gh['branch']}. The sync to "
                    "ossie-semantic-contracts starts right away."
                )

                gh_message = st.text_input(
                    "Commit message",
                    value=f"Update {gh['folder']}/{filename}",
                    key="gen_gh_msg",
                )

                if st.button(
                    "Publish to GitHub",
                    type="primary",
                    icon=":material/cloud_upload:",
                    width="stretch",
                    key="gen_gh_save",
                    disabled=unchanged,
                    help="Nothing new to publish." if unchanged else None,
                ):
                    with st.spinner("Publishing to GitHub..."):
                        try:
                            # Keep the local copy in step with what goes to GitHub
                            save_yaml(filename, yaml_text)
                            save_section("model", {**st.session_state.saved["model"],
                                                   "source_file": filename})
                            result = github_service.save_file(
                                filename, yaml_text,
                                message=gh_message.strip() or None,
                                mode=modes[choice],
                            )
                        except github_service.GitHubError as exc:
                            result = {"status": "error", "error": str(exc)}
                        except Exception as exc:
                            result = {"status": "error", "error": f"Couldn't reach GitHub: {exc}"}
                    result["for"] = yaml_hash
                    st.session_state.gh_result = result
                    if result["status"] != "error":
                        # Forget the stored copy of the GitHub file, for every session
                        _github_version.clear()
                        st.session_state.gh_refresh = st.session_state.get("gh_refresh", 0) + 1
                        # Follow this publish through both repos
                        st.session_state.sync_track = {**result, "for": yaml_hash}
                        st.session_state.sync_polling = True
                        st.session_state.sync_started = time.time()
                    st.rerun()

                result = st.session_state.get("gh_result")
                if result and result.get("for") == yaml_hash:
                    if result["status"] == "error":
                        st.error(result["error"])
                    elif result["status"] == "pull_request":
                        st.success(f"Pull request opened. [Review and merge it]({result['url']})")
                    elif result["status"] == "committed":
                        st.success(f"Published to {gh['branch']}. [View the commit]({result['url']})")
                    else:
                        st.info(f"GitHub already has this version. [View it]({result['url']})")

            else:
                st.markdown(
                    '<p class="cx-hint">Publishing to GitHub isn\'t set up. Add a '
                    '[github] section to the app\'s secrets (see README).</p>',
                    unsafe_allow_html=True,
                )
                if st.button(
                    "Save to outputs", type="primary", icon=":material/save:",
                    width="stretch", disabled=unchanged, key="gen_local_save",
                ):
                    save_yaml(filename, yaml_text)
                    save_section("model", {**st.session_state.saved["model"],
                                           "source_file": filename})
                    st.toast(f"Saved outputs/{filename}")
                    st.rerun()

            st.download_button(
                "Download YAML",
                data=yaml_text,
                file_name=filename,
                mime="text/yaml",
                icon=":material/download:",
                width="stretch",
            )

    #################################################
    # SYNC STATUS
    #################################################

    if gh:
        render_sync_status(gh, yaml_text, yaml_hash)

#################################################
# ADVANCED
#################################################

st.write("")

with st.expander("Advanced: export, load or reset the configuration"):

    st.caption(
        "Your saved steps reload automatically. Export them to share a model "
        "or reuse it later."
    )

    a1, a2 = st.columns(2, gap="large")

    with a1:
        st.download_button(
            "Export configuration",
            data=config_json(),
            file_name=f"{saved['model']['name'] or 'model'}_config.json",
            mime="application/json",
            icon=":material/file_download:",
        )
        uploaded = st.file_uploader("Load a configuration file", type=["json"])
        if uploaded is not None and st.button("Load configuration"):
            try:
                replace_config(json.loads(uploaded.getvalue().decode("utf-8")))
                st.rerun()
            except ValueError as exc:
                st.error(f"That file isn't a valid configuration: {exc}")

    with a2:
        st.markdown("**Start over**")
        confirm = st.checkbox("Clear all saved datasets, relationships and metrics")
        if st.button("Clear everything", disabled=not confirm):
            reset_config()
            st.rerun()

nav_bar(back="metrics")
