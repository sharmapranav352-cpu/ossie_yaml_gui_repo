"""
Tracks a published SIT_YAML_GUI.yaml through both repositories:

  1. ossie_yaml_gui_repo        the file is on main (after the PR is merged, if any)
  2. Sync workflow              "Sync to ossie-semantic-contracts" runs for that commit
  3. ossie-semantic-contracts   the file there matches (after its PR is merged, if any)

"In sync" means the file on both main branches is byte-for-byte the YAML that
was published. Everything here is read-only.

Each stage is a dict: key, label, state, detail, url
  state: "done" | "active" | "waiting" | "error" | "pending"
"""

import base64

import requests

API = "https://api.github.com"
TIMEOUT = 20
SYNC_BRANCH = "sync/sit-yaml-gui"   # branch the sync workflow uses for its PRs


class _NoAccess(Exception):
    pass


def _get(repo, path, token=None, params=None):
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    resp = requests.request(
        "GET", f"{API}/repos/{repo}{path}",
        headers=headers, params=params, timeout=TIMEOUT,
    )
    if resp.status_code == 404:
        return None
    if resp.status_code in (401, 403):
        raise _NoAccess(resp.status_code)
    resp.raise_for_status()
    return resp.json()


def _file_text(repo, path, branch, token):
    data = _get(repo, f"/contents/{path}", token, {"ref": branch})
    if not data:
        return None
    return base64.b64decode(data["content"]).decode("utf-8")


def _short(sha):
    return sha[:7] if sha else ""


def check(cfg, yaml_text, publish):
    """
    cfg      github_service.settings()
    publish  what the app published this session, or None to just compare:
             {"status": "committed"|"pull_request", "sha", "pr_number", "url"}
    Returns (stages, overall): "done" | "active" | "waiting" | "error" | "idle"
    ("idle" = this YAML isn't published, so there is nothing to follow).
    """
    src, tgt = cfg["repo"], cfg["contracts_repo"]
    src_tok, tgt_tok = cfg["token"], cfg["contracts_token"]
    src_path = f"{cfg['folder']}/{_file_name(publish, cfg)}"
    src_name, tgt_name = src.split("/")[-1], tgt.split("/")[-1]
    publish = publish or {}

    stages = [
        {"key": "source", "label": f"Saved in {src_name}", "state": "pending", "detail": "", "url": None},
        {"key": "sync", "label": "Sync workflow", "state": "pending", "detail": "", "url": None},
        {"key": "target", "label": f"Updated in {tgt_name}", "state": "pending", "detail": "", "url": None},
    ]
    s_src, s_sync, s_tgt = stages

    # ---- 1. source repo -----------------------------------------------------
    main_sha = publish.get("sha")
    src_text = _file_text(src, src_path, cfg["branch"], src_tok)

    if src_text == yaml_text:
        s_src.update(state="done", detail=f"{src_path} is on {cfg['branch']}.",
                     url=f"https://github.com/{src}/blob/{cfg['branch']}/{src_path}")
        if publish.get("pr_number"):
            pr = _get(src, f"/pulls/{publish['pr_number']}", src_tok) or {}
            main_sha = pr.get("merge_commit_sha") or main_sha
            s_src["detail"] = f"Pull request #{publish['pr_number']} merged."
            s_src["url"] = pr.get("html_url") or s_src["url"]
    elif publish.get("pr_number"):
        pr = _get(src, f"/pulls/{publish['pr_number']}", src_tok) or {}
        if pr.get("state") == "closed" and not pr.get("merged_at"):
            s_src.update(state="error", url=pr.get("html_url"),
                         detail=f"Pull request #{publish['pr_number']} was closed without merging.")
        else:
            s_src.update(state="waiting", url=pr.get("html_url") or publish.get("url"),
                         detail=f"Waiting for you to merge pull request #{publish['pr_number']}.")
        return stages, s_src["state"]
    else:
        if not publish:
            s_src.update(state="pending", detail=(
                f"{src_path} on {cfg['branch']} doesn't match this YAML yet. "
                "Publish it to start the sync."))
            return stages, "idle"
        s_src.update(state="active", detail="Saving to GitHub...")
        return stages, "active"

    if not main_sha:
        # Not published in this session: follow the latest commit to the file
        commits = _get(src, "/commits", src_tok,
                       {"path": src_path, "sha": cfg["branch"], "per_page": 1}) or []
        main_sha = commits[0]["sha"] if commits else None

    # ---- 3 first: is the contracts repo already up to date? -----------------
    try:
        tgt_text = _file_text(tgt, cfg["contracts_file"], cfg["contracts_branch"], tgt_tok)
        # GitHub answers "not found" for private repos it won't show you
        tgt_readable = tgt_text is not None
    except _NoAccess:
        tgt_text, tgt_readable = None, False

    if tgt_text == yaml_text:
        s_tgt.update(state="done", detail=f"{cfg['contracts_file']} matches.",
                     url=f"https://github.com/{tgt}/blob/{cfg['contracts_branch']}/{cfg['contracts_file']}")
        s_sync.update(state="done", detail="Finished.")
        _attach_run(cfg, main_sha, s_sync, finished_ok=True)
        return stages, "done"

    # ---- 2. sync workflow ------------------------------------------------------
    _attach_run(cfg, main_sha, s_sync, finished_ok=False)

    # ---- 3. contracts repo -------------------------------------------------------
    if not tgt_readable:
        s_tgt.update(state="error", detail=(
            f"Can't read {cfg['contracts_file']} in {tgt}. If that repository "
            "is private, add a read-only contracts_token to the app's secrets "
            "(see README)."))
        return stages, "error"

    if s_sync["state"] == "error":
        s_tgt.update(state="pending", detail="Waiting on the sync workflow.")
        return stages, "error"

    owner = tgt.split("/")[0]
    prs = _get(tgt, "/pulls", tgt_tok,
               {"head": f"{owner}:{SYNC_BRANCH}", "state": "open"}) or []
    if prs:
        pr = prs[0]
        s_tgt.update(state="waiting", url=pr.get("html_url"),
                     detail=f"Waiting for pull request #{pr.get('number')} to be merged there.")
        if s_sync["state"] in ("active", "pending"):
            s_sync.update(state="done", detail="Finished and opened a pull request.")
        return stages, "waiting"

    s_tgt.update(state="active" if s_sync["state"] == "done" else "pending",
                 detail="Waiting for the file to be updated...")
    return stages, "active"


def _attach_run(cfg, sha, stage, finished_ok):
    """Fill the sync stage from the workflow run for this commit, if visible."""
    if not sha:
        if not finished_ok:
            stage.update(state="active", detail="Waiting for the sync workflow to start...")
        return
    try:
        data = _get(cfg["repo"], f"/actions/workflows/{cfg['sync_workflow']}/runs",
                    cfg["token"], {"head_sha": sha, "per_page": 1}) or {}
    except _NoAccess:
        if not finished_ok:
            stage.update(state="active", detail=(
                "Running. (Give the app's GitHub token Actions: Read to see "
                "the workflow's progress here.)"))
        return

    runs = data.get("workflow_runs") or []
    if not runs:
        if not finished_ok:
            stage.update(state="active", detail=f"Waiting for the run for {_short(sha)} to start...")
        return

    run = runs[0]
    stage["url"] = run.get("html_url")
    status, conclusion = run.get("status"), run.get("conclusion")

    if status != "completed":
        stage.update(state="active",
                     detail="Queued..." if status in ("queued", "waiting", "pending") else "Running...")
    elif conclusion == "success":
        stage.update(state="done", detail="Finished.")
    else:
        stage.update(state="error", detail=f"The run ended with '{conclusion}'. Open it for details.")


def _file_name(publish, cfg):
    from utils.file_manager import FIXED_OUTPUT_FILE
    return FIXED_OUTPUT_FILE or (publish or {}).get("file") or "SIT_YAML_GUI.yaml"
