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
