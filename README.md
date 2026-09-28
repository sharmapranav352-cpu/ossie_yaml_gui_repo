# Project Compass: Semantic Model Builder

A Streamlit app by Pranav that builds an OSSIE semantic model YAML
from Snowflake tables, in five steps: connect, choose datasets, define
relationships, add metrics, and generate the YAML.

## Run it

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Branding

- Logos: add `assets/compass_logo.svg` (or `.png`) for the top of the
  front page, and `assets/snap_logo.svg` (or `.png`) for the bottom-right
  corner of every page. See `assets/README.md`.
- Colours and fonts: `.streamlit/config.toml`. Change `primaryColor` to
  restyle every accent in the app.

## Saving YAML to GitHub

The Generate YAML page can save the file straight into this repository
(`outputs/`), either as a pull request or as a direct commit.

1. Create a fine-grained GitHub token for this repository only, with
   **Contents** and **Pull requests** set to **Read and write**.
2. Add it to the app's secrets. Locally, in `.streamlit/secrets.toml`
   (git-ignored); on Streamlit Cloud, under App settings > Secrets:

   ```toml
   [github]
   token  = "github_pat_..."
   repo   = "sharmapranav352-cpu/ossie_yaml_gui_repo"
   branch = "main"
   folder = "outputs"
   mode   = "pull_request"   # or "direct"
   ```

Never commit the token to the repository.

## Ossie format and syncing to ossie-semantic-contracts

The app writes standard Apache Ossie YAML, version `0.2.0.dev0`, with the
model at the top level (no `semantic_model:` wrapper). The file is always
`outputs/SIT_YAML_GUI.yaml` and the model is always named `SIT_TEST1`.

When `outputs/SIT_YAML_GUI.yaml` changes on `main`, the
*Sync to ossie-semantic-contracts* workflow checks it, runs it through that
repo's Snowflake converter, and copies it to
`project-compass-SIT/ossie-semantic-contracts` as
`ossie_yaml/SIT_TEST1_0.2.0.dev0_ossie.yaml`. By default it opens a pull
request there, because merging it deploys the semantic view to Snowflake.

Setup, in this repo's Settings > Secrets and variables > Actions:

- Secret `CONTRACTS_REPO_TOKEN`: fine-grained token for
  `project-compass-SIT/ossie-semantic-contracts` with Contents and
  Pull requests set to Read and write.
- Optional variable `CONTRACTS_SYNC_MODE`: `pull_request` (default) or
  `direct` to commit straight to that repo's `main`.
