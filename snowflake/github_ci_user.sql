-- =====================================================================
-- Snowflake setup for the "Semantic view sync" GitHub workflow
--
-- GitHub Actions signs in as GITHUB_CI (key-pair auth, no password or
-- MFA) on a schedule, exports every semantic view in the database, and
-- starts a build when any of them changed.
--
-- Run as ACCOUNTADMIN. Replace everything in <ANGLE_BRACKETS> first.
-- =====================================================================

USE ROLE ACCOUNTADMIN;

-- Role that can read semantic view definitions -------------------------
CREATE ROLE IF NOT EXISTS GITHUB_CI_ROLE;

GRANT USAGE ON DATABASE <YOUR_DATABASE> TO ROLE GITHUB_CI_ROLE;
GRANT USAGE ON ALL SCHEMAS IN DATABASE <YOUR_DATABASE> TO ROLE GITHUB_CI_ROLE;
GRANT USAGE ON FUTURE SCHEMAS IN DATABASE <YOUR_DATABASE> TO ROLE GITHUB_CI_ROLE;
GRANT REFERENCES ON ALL SEMANTIC VIEWS IN DATABASE <YOUR_DATABASE> TO ROLE GITHUB_CI_ROLE;
GRANT REFERENCES ON FUTURE SEMANTIC VIEWS IN DATABASE <YOUR_DATABASE> TO ROLE GITHUB_CI_ROLE;
GRANT USAGE ON WAREHOUSE <YOUR_WAREHOUSE> TO ROLE GITHUB_CI_ROLE;

-- Service user GitHub signs in as --------------------------------------
CREATE USER IF NOT EXISTS GITHUB_CI
  TYPE = SERVICE
  DEFAULT_ROLE = GITHUB_CI_ROLE
  DEFAULT_WAREHOUSE = <YOUR_WAREHOUSE>
  RSA_PUBLIC_KEY = '<PUBLIC_KEY_WITHOUT_BEGIN_END_LINES>';

GRANT ROLE GITHUB_CI_ROLE TO USER GITHUB_CI;

-- Keep compute cost low: the warehouse suspends 60 seconds after each check
ALTER WAREHOUSE <YOUR_WAREHOUSE> SET AUTO_SUSPEND = 60 AUTO_RESUME = TRUE;

-- Check: should list GITHUB_CI with TYPE = SERVICE and HAS_RSA_PUBLIC_KEY = true
SHOW USERS LIKE 'GITHUB_CI';
