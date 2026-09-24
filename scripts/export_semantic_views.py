"""
Export Snowflake semantic views to YAML files in semantic_views/.

Called by .github/workflows/semantic-view-changed.yml.

Environment variables:
  SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, SNOWFLAKE_PRIVATE_KEY (PEM text),
  SNOWFLAKE_ROLE, SNOWFLAKE_WAREHOUSE
  SV_DATABASE  database to export
  SV_CHANGED   JSON list of fully qualified view names that changed;
               "null" or empty means export every view in SV_DATABASE
  SV_DROPPED   JSON list of fully qualified view names that were dropped
"""

import json
import os
from pathlib import Path

import snowflake.connector
from cryptography.hazmat.primitives import serialization

OUT_DIR = Path("semantic_views")

# Plain Snowflake YAML. For Ossie YAML, switch to the Ossie export function
# your account supports (see SYSTEM$READ_OSSIE_YAML_FROM_SEMANTIC_VIEW in
# the Snowflake docs).
EXPORT_FUNCTION = "SYSTEM$READ_YAML_FROM_SEMANTIC_VIEW"


def json_list(name):
    raw = os.environ.get(name, "").strip()
    if not raw or raw == "null":
        return None
    return json.loads(raw)


def split_fqn(fqn):
    """'"DB"."SCHEMA"."VIEW"' -> ('DB', 'SCHEMA', 'VIEW')"""
    parts, buf, in_quotes, i = [], "", False, 0
    while i < len(fqn):
        ch = fqn[i]
        if ch == '"':
            if in_quotes and i + 1 < len(fqn) and fqn[i + 1] == '"':
                buf += '"'
                i += 1
            else:
                in_quotes = not in_quotes
        elif ch == "." and not in_quotes:
            parts.append(buf)
            buf = ""
        else:
            buf += ch
        i += 1
    parts.append(buf)
    return tuple(parts)


def file_for(fqn):
    db, schema, view = split_fqn(fqn)
    return OUT_DIR / db / schema / f"{view}.yaml"


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


def main():
    database = os.environ["SV_DATABASE"]
    changed = json_list("SV_CHANGED")
    dropped = json_list("SV_DROPPED") or []

    conn = connect()
    cur = conn.cursor()

    try:
        if changed is None:
            # Manual run: export everything in the database
            cur.execute(f"SHOW SEMANTIC VIEWS IN DATABASE {q(database)}")
            cols = [c[0].lower() for c in cur.description]
            rows = [dict(zip(cols, r)) for r in cur.fetchall()]
            changed = [
                f'{q(r["database_name"])}.{q(r["schema_name"])}.{q(r["name"])}'
                for r in rows
            ]

        for fqn in changed:
            cur.execute(f"SELECT {EXPORT_FUNCTION}(%s)", (fqn,))
            spec = cur.fetchone()[0]
            path = file_for(fqn)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(spec, encoding="utf-8")
            print(f"Exported {fqn} -> {path}")

        for fqn in dropped:
            path = file_for(fqn)
            if path.exists():
                path.unlink()
                print(f"Removed {path} ({fqn} was dropped)")

    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
