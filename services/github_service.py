"""
Save generated YAML files to the GitHub repository through GitHub's REST API.

Settings come from Streamlit secrets (never from the code or the repo):

    [github]
    token  = "github_pat_..."                       # fine-grained token
    repo   = "sharmapranav352-cpu/ossie_yaml_gui_repo"
    branch = "main"                                  # optional, default "main"
    folder = "outputs"                               # optional, default "outputs"
    mode   = "pull_request"                          # or "direct"

Locally: .streamlit/secrets.toml (git-ignored).
Streamlit Cloud: App settings > Secrets.
"""

import base64
import re
from datetime import datetime, timezone

import requests
import streamlit as st

API = "https://api.github.com"
TIMEOUT = 30


class GitHubError(Exception):
    pass


##################################################
# SETTINGS
##################################################

def settings():
    """Return the [github] settings, or None if they aren't set up."""
    try:
        cfg = dict(st.secrets.get("github", {}))
    except Exception:
        return None

    if not cfg.get("token") or not cfg.get("repo"):
        return None

    return {
        "token": cfg["token"],
        "repo": cfg["repo"].strip().strip("/"),
        "branch": cfg.get("branch", "main"),
        "folder": cfg.get("folder", "outputs").strip("/"),
        "mode": cfg.get("mode", "pull_request"),
    }


def is_configured():
    return settings() is not None


##################################################
# LOW-LEVEL API
##################################################

def _request(method, path, cfg, **kwargs):
    resp = requests.request(
        method,
        f"{API}/repos/{cfg['repo']}{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {cfg['token']}",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        timeout=TIMEOUT,
        **kwargs,
    )

    if resp.status_code in (401, 403):
        raise GitHubError(
            "GitHub refused the request. Check that the token is valid, "
            "not expired, and has Contents and Pull requests set to "
            "Read and write for this repository."
        )
    if resp.status_code == 404 and method == "GET" and "/contents/" in path:
        return None
    if resp.status_code == 404:
        raise GitHubError(
            f"GitHub couldn't find {cfg['repo']}. Check the repo name in "
            "the secrets and that the token has access to it."
        )
    if resp.status_code >= 400:
        try:
            msg = resp.json().get("message", resp.text)
        except ValueError:
            msg = resp.text
        raise GitHubError(f"GitHub error {resp.status_code}: {msg}")

    return resp.json() if resp.content else {}


def _get_file(cfg, path, ref):
    """(text, sha) of a file on a branch, or (None, None) if it doesn't exist."""
    data = _request("GET", f"/contents/{path}", cfg, params={"ref": ref})
    if not data:
        return None, None
    text = base64.b64decode(data["content"]).decode("utf-8")
    return text, data["sha"]


def _branch_sha(cfg, branch):
    data = _request("GET", f"/git/ref/heads/{branch}", cfg)
    return data["object"]["sha"]


def _create_branch(cfg, name, from_branch):
    _request(
        "POST", "/git/refs", cfg,
        json={"ref": f"refs/heads/{name}", "sha": _branch_sha(cfg, from_branch)},
    )


def _put_file(cfg, path, text, message, branch, sha=None):
    body = {
        "message": message,
        "content": base64.b64encode(text.encode("utf-8")).decode("ascii"),
        "branch": branch,
    }
    if sha:
        body["sha"] = sha
    return _request("PUT", f"/contents/{path}", cfg, json=body)


def _open_pr(cfg, head, title, body):
    return _request(
        "POST", "/pulls", cfg,
        json={"title": title, "head": head, "base": cfg["branch"], "body": body},
    )


##################################################
# PUBLIC
##################################################

def read_file(filename):
    """Current text of <folder>/<filename> on the main branch, or None."""
    cfg = settings()
    if not cfg:
        return None
    text, _ = _get_file(cfg, f"{cfg['folder']}/{filename}", cfg["branch"])
    return text


def save_file(filename, text, message=None, mode=None):
    """
    Save <folder>/<filename> to GitHub.

    mode "pull_request": new branch + commit + pull request (nothing reaches
                         main until someone merges it on GitHub)
    mode "direct":       commit straight to the main branch

    Returns {"status": "unchanged" | "committed" | "pull_request",
             "url": link to show the user, "path": repo path}
    """
    cfg = settings()
    if not cfg:
        raise GitHubError("GitHub isn't set up. Add a [github] section to the app's secrets.")

    mode = mode or cfg["mode"]
    path = f"{cfg['folder']}/{filename}"
    repo_url = f"https://github.com/{cfg['repo']}"

    current, sha = _get_file(cfg, path, cfg["branch"])
    if current == text:
        return {
            "status": "unchanged",
            "url": f"{repo_url}/blob/{cfg['branch']}/{path}",
            "path": path,
        }

    action = "Update" if current is not None else "Add"
    message = message or f"{action} {path} from Semantic Model Builder"

    if mode == "direct":
        result = _put_file(cfg, path, text, message, cfg["branch"], sha)
        return {
            "status": "committed",
            "url": result["commit"]["html_url"],
            "path": path,
        }

    # Pull request: one new branch per save
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    slug = re.sub(r"[^A-Za-z0-9_-]", "-", filename.rsplit(".", 1)[0])[:40]
    branch = f"yaml/{slug}-{stamp}"

    _create_branch(cfg, branch, cfg["branch"])
    _put_file(cfg, path, text, message, branch, sha)
    pr = _open_pr(
        cfg, branch,
        title=message,
        body=(
            f"{action}s `{path}` from the Semantic Model Builder app.\n\n"
            "Review the changes under **Files changed**, then merge."
        ),
    )
    return {"status": "pull_request", "url": pr["html_url"], "path": path}
