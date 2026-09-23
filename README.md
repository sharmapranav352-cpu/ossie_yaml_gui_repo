# Semantic Model Builder

A Streamlit app by Snap Analytics that builds an OSSIE semantic model YAML
from Snowflake tables, in five steps: connect, choose datasets, define
relationships, add metrics, and generate the YAML.

## Run it

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Branding

- Logo: add `assets/snap_logo.svg` or `assets/snap_logo.png`
  (see `assets/README.md`).
- Colours and fonts: `.streamlit/config.toml`. Change `primaryColor` to
  restyle every accent in the app.
