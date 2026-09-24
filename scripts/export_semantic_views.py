"""
Export every semantic view in a Snowflake database to
semantic_views/<database>/<schema>/<view>.yaml, and report what changed.

The YAML files already in the repo are the "last known" state, so a view
counts as changed when its exported YAML differs from the file on disk.
Files for views that no longer exist are deleted.

Environment variables:
  SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, SNOWFLAKE_PRIVATE_KEY (PEM text),
  SNOWFLAKE_ROLE, SNOWFLAKE_WAREHOUSE, SV_DATABASE

Writes changed / changed_views / dropped_views to $GITHUB_OUTPUT.
"""

import os
from pathlib import Path

import snowflake.connector
from cryptography.hazmat.primitives import serialization

OUT_DIR = Path("semantic_views")

# Plain Snowflake YAML. For Ossie YAML, switch to the Ossie export function
# your account supports (see SYSTEM$READ_OSSIE_YAML_FROM_SEMANTIC_VIEW in
# the Snowflake docs).
EXPORT_FUNCTION = "SYSTEM$READ_YAML_FROM_SEMANTIC_VIEW"


def q(name):
    return '"' + name.replace('"', '""') + '"'


def connect():
    key = serialization.load_pem_private_key(
        os.environ["SNOWFLAKE_PRIVATE_KEY"].encode(), password=None
    )
    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        private_key=key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ),
        role=os.environ.get("SNOWFLAKE_ROLE") or None,
        warehouse=os.environ.get("SNOWFLAKE_WAREHOUSE") or None,
    )


def set_output(name, value):
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"{name}={value}\n")


def main():
    database = os.environ.get("SV_DATABASE", "").strip()
    if not database:
        raise SystemExit(
            "SV_DATABASE is not set. Add it under Settings > Secrets and "
            "variables > Actions > Variables."
        )

    db_dir = OUT_DIR / database
    before = {p for p in db_dir.rglob("*.yaml")} if db_dir.exists() else set()

    changed, seen = [], set()

    conn = connect()
    cur = conn.cursor()
    try:
        cur.execute(f"SHOW SEMANTIC VIEWS IN DATABASE {q(database)}")
        cols = [c[0].lower() for c in cur.description]
        views = [dict(zip(cols, r)) for r in cur.fetchall()]
        print(f"Found {len(views)} semantic view(s) in {database}")

        for v in views:
            fqn = f'{q(v["database_name"])}.{q(v["schema_name"])}.{q(v["name"])}'
            cur.execute(f"SELECT {EXPORT_FUNCTION}(%s)", (fqn,))
            spec = cur.fetchone()[0]

            path = OUT_DIR / v["database_name"] / v["schema_name"] / f'{v["name"]}.yaml'
            seen.add(path)

            old = path.read_text(encoding="utf-8") if path.exists() else None
            if old != spec:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(spec, encoding="utf-8")
                changed.append(f'{v["schema_name"]}.{v["name"]}')
                print(f"{'Updated' if old is not None else 'New'}: {fqn}")
    finally:
        cur.close()
        conn.close()

    dropped = []
    for path in sorted(before - seen):
        path.unlink()
        dropped.append(f"{path.parent.name}.{path.stem}")
        print(f"Dropped: {path}")

    any_change = bool(changed or dropped)
    set_output("changed", "true" if any_change else "false")
    set_output("changed_views", ", ".join(changed) or "none")
    set_output("dropped_views", ", ".join(dropped) or "none")

    print(f"Changed or new: {len(changed)}, dropped: {len(dropped)}")


if __name__ == "__main__":
    main()
