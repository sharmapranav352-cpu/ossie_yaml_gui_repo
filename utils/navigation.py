"""Single list of the app's pages, used by the router, progress bar and 'continue' links."""

PAGES = [
    {"key": "connect",       "path": "pages/0_Connect.py",       "title": "Connect",       "icon": ":material/cable:"},
    {"key": "datasets",      "path": "pages/1_Datasets.py",      "title": "Datasets",      "icon": ":material/table:"},
    {"key": "relationships", "path": "pages/2_Relationships.py", "title": "Relationships", "icon": ":material/hub:"},
    {"key": "metrics",       "path": "pages/3_Metrics.py",       "title": "Metrics",       "icon": ":material/functions:"},
    {"key": "generate",      "path": "pages/4_Generate_YAML.py", "title": "Generate YAML", "icon": ":material/description:"},
]

BY_KEY = {p["key"]: p for p in PAGES}
