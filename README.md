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
