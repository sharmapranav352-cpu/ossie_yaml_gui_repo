-- =====================================================================
-- Trigger a GitHub Actions build when a Snowflake semantic view changes
--
-- How it works:
--   A task runs every 5 minutes. It reads each semantic view's YAML spec,
--   hashes it, and compares with the hash from the last run. If anything
--   was created, changed or dropped, it calls GitHub's repository_dispatch
--   REST API, which starts the "Semantic view changed" workflow.
--
-- Run this as ACCOUNTADMIN (or a role that can create integrations).
-- Replace everything in <ANGLE_BRACKETS> first.
-- =====================================================================

USE ROLE ACCOUNTADMIN;

CREATE DATABASE IF NOT EXISTS OPS;
CREATE SCHEMA IF NOT EXISTS OPS.SEMANTIC_SYNC;
USE SCHEMA OPS.SEMANTIC_SYNC;

-- 1. Allow outbound calls to the GitHub API only -----------------------
CREATE OR REPLACE NETWORK RULE GITHUB_API_RULE
  MODE = EGRESS
  TYPE = HOST_PORT
  VALUE_LIST = ('api.github.com');

-- 2. Store the GitHub token as a secret ---------------------------------
-- Fine-grained token, this repository only, permission:
--   Contents: Read and write   (required for repository_dispatch)
CREATE OR REPLACE SECRET GITHUB_TOKEN
  TYPE = GENERIC_STRING
  SECRET_STRING = '<GITHUB_FINE_GRAINED_TOKEN>';

CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION GITHUB_API_ACCESS
  ALLOWED_NETWORK_RULES = (GITHUB_API_RULE)
  ALLOWED_AUTHENTICATION_SECRETS = (GITHUB_TOKEN)
  ENABLED = TRUE;

-- 3. Remember what each semantic view looked like last time -------------
CREATE TABLE IF NOT EXISTS SEMANTIC_VIEW_STATE (
  DATABASE_NAME STRING,
  VIEW_NAME     STRING,      -- fully qualified, quoted
  SPEC_HASH     STRING,
  CHECKED_AT    TIMESTAMP_LTZ
);

-- 4. Detect changes and call GitHub -------------------------------------
CREATE OR REPLACE PROCEDURE CHECK_SEMANTIC_VIEWS(DB STRING)
  RETURNS VARIANT
  LANGUAGE PYTHON
  RUNTIME_VERSION = '3.11'
  PACKAGES = ('snowflake-snowpark-python', 'requests')
  HANDLER = 'run'
  EXTERNAL_ACCESS_INTEGRATIONS = (GITHUB_API_ACCESS)
  SECRETS = ('gh' = GITHUB_TOKEN)
  EXECUTE AS OWNER
AS
$$
import hashlib
import requests
import _snowflake
from snowflake.snowpark.functions import current_timestamp

GITHUB_OWNER = "sharmapranav352-cpu"
GITHUB_REPO = "ossie_yaml_gui_repo"
EVENT_TYPE = "semantic_view_changed"


def q(name):
    return '"' + name.replace('"', '""') + '"'


def run(session, db):
    # Current state: hash of every semantic view's YAML spec
    views = session.sql(f"SHOW SEMANTIC VIEWS IN DATABASE {q(db)}").collect()
    current = {}
    for v in views:
        fqn = f'{q(v["database_name"])}.{q(v["schema_name"])}.{q(v["name"])}'
        spec = session.sql(
            "SELECT SYSTEM$READ_YAML_FROM_SEMANTIC_VIEW(?)", params=[fqn]
        ).collect()[0][0]
        current[fqn] = hashlib.sha256(spec.encode("utf-8")).hexdigest()

    # Last known state
    rows = session.sql(
        "SELECT VIEW_NAME, SPEC_HASH FROM SEMANTIC_VIEW_STATE WHERE DATABASE_NAME = ?",
        params=[db],
    ).collect()
    known = {r["VIEW_NAME"]: r["SPEC_HASH"] for r in rows}

    first_run = not known
    changed = sorted(n for n, h in current.items() if known.get(n) != h)
    dropped = sorted(n for n in known if n not in current)

    dispatched = False
    if (changed or dropped) and not first_run:
        resp = requests.post(
            f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/dispatches",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {_snowflake.get_generic_secret_string('gh')}",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            json={
                "event_type": EVENT_TYPE,
                "client_payload": {
                    "database": db,
                    "changed": changed,
                    "dropped": dropped,
                },
            },
            timeout=30,
        )
        # GitHub returns 204 on success. If it fails we raise, the state
        # is not updated, and the next run tries again.
        if resp.status_code != 204:
            raise Exception(f"GitHub dispatch failed: {resp.status_code} {resp.text}")
        dispatched = True

    # Save the new state (first run just records a baseline)
    session.sql("DELETE FROM SEMANTIC_VIEW_STATE WHERE DATABASE_NAME = ?", params=[db]).collect()
    if current:
        session.create_dataframe(
            [[db, n, h] for n, h in current.items()],
            schema=["DATABASE_NAME", "VIEW_NAME", "SPEC_HASH"],
        ).with_column("CHECKED_AT", current_timestamp()).write.save_as_table(
            "SEMANTIC_VIEW_STATE", mode="append", column_order="name"
        )

    return {
        "database": db,
        "views": len(current),
        "baseline_only": first_run,
        "changed": changed,
        "dropped": dropped,
        "dispatched": dispatched,
    }
$$;

-- 5. Test it by hand ----------------------------------------------------
-- First call records a baseline and does not trigger GitHub.
CALL CHECK_SEMANTIC_VIEWS('<YOUR_DATABASE>');
-- Change a semantic view (e.g. ALTER SEMANTIC VIEW ... SET COMMENT = 'test')
-- and call again: "dispatched" should be true and a workflow run should start.
CALL CHECK_SEMANTIC_VIEWS('<YOUR_DATABASE>');

-- 6. Run it automatically every 5 minutes -------------------------------
-- Serverless task: no warehouse to keep awake. To use a warehouse instead,
-- add  WAREHOUSE = <YOUR_WAREHOUSE>  and remove the size line.
CREATE OR REPLACE TASK CHECK_SEMANTIC_VIEWS_TASK
  USER_TASK_MANAGED_INITIAL_WAREHOUSE_SIZE = 'XSMALL'
  SCHEDULE = '5 MINUTE'
AS
  CALL CHECK_SEMANTIC_VIEWS('<YOUR_DATABASE>');

ALTER TASK CHECK_SEMANTIC_VIEWS_TASK RESUME;

-- Check recent runs
-- SELECT * FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY(TASK_NAME => 'CHECK_SEMANTIC_VIEWS_TASK'))
-- ORDER BY SCHEDULED_TIME DESC LIMIT 20;

-- =====================================================================
-- 7. Service user for GitHub Actions to read the semantic views back
--    (key-pair auth: no password or MFA prompts in CI)
-- =====================================================================
CREATE ROLE IF NOT EXISTS GITHUB_CI_ROLE;
GRANT USAGE ON DATABASE <YOUR_DATABASE> TO ROLE GITHUB_CI_ROLE;
GRANT USAGE ON ALL SCHEMAS IN DATABASE <YOUR_DATABASE> TO ROLE GITHUB_CI_ROLE;
GRANT REFERENCES ON ALL SEMANTIC VIEWS IN DATABASE <YOUR_DATABASE> TO ROLE GITHUB_CI_ROLE;
GRANT REFERENCES ON FUTURE SEMANTIC VIEWS IN DATABASE <YOUR_DATABASE> TO ROLE GITHUB_CI_ROLE;
GRANT USAGE ON WAREHOUSE <YOUR_WAREHOUSE> TO ROLE GITHUB_CI_ROLE;

CREATE USER IF NOT EXISTS GITHUB_CI
  TYPE = SERVICE
  DEFAULT_ROLE = GITHUB_CI_ROLE
  DEFAULT_WAREHOUSE = <YOUR_WAREHOUSE>
  RSA_PUBLIC_KEY = '<PUBLIC_KEY_WITHOUT_BEGIN_END_LINES>';

GRANT ROLE GITHUB_CI_ROLE TO USER GITHUB_CI;
