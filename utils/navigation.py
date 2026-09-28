"""Single list of the app's pages, used by the router, progress bar and 'continue' links."""

PAGES = [
    {"key": "connect",       "path": "views/0_Connect.py",       "title": "Connect",       "icon": ":material/cable:"},
    {"key": "datasets",      "path": "views/1_Datasets.py",      "title": "Datasets",      "icon": ":material/table:"},
    {"key": "relationships", "path": "views/2_Relationships.py", "title": "Relationships", "icon": ":material/hub:"},
    {"key": "metrics",       "path": "views/3_Metrics.py",       "title": "Metrics",       "icon": ":material/functions:"},
    {"key": "publish",       "path": "views/4_Generate_YAML.py", "title": "Publish",       "icon": ":material/publish:"},
]

BY_KEY = {p["key"]: p for p in PAGES}
