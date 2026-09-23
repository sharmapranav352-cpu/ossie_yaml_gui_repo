import snowflake.connector
import pandas as pd


class SnowflakeService:

    def __init__(
        self,
        account,
        username,
        password=None,
        warehouse=None,
        role=None,
        authenticator="snowflake",
        passcode=None
    ):
        """
        authenticator options:
          - "snowflake"              : standard username/password, no MFA
          - "username_password_mfa"  : username/password + TOTP passcode
                                        (also lets Snowflake cache the MFA
                                        token so you aren't prompted every time)
          - "externalbrowser"        : SSO / browser-based login (opens a
                                        browser window on the machine running
                                        the app -- only works if that machine
                                        has a browser, e.g. local dev, not
                                        headless servers)

        For plain Duo Push (no code, just approve on your phone), you don't
        need any of the above -- use authenticator="snowflake" with password,
        and Snowflake will trigger the push automatically if Duo is enabled
        for your account/role. The connector call will block until you
        approve or it times out.
        """

        connect_kwargs = {
            "account": account,
            "user": username,
            "warehouse": warehouse,
            "role": role,
            "authenticator": authenticator,
        }

        if password:
            connect_kwargs["password"] = password

        if authenticator == "username_password_mfa" and passcode:
            connect_kwargs["passcode"] = passcode

        self.conn = snowflake.connector.connect(**connect_kwargs)

    def execute(
        self,
        sql
    ):

        cursor = self.conn.cursor()

        try:

            cursor.execute(sql)

            rows = cursor.fetchall()

            cols = (
                [x[0] for x in cursor.description]
                if cursor.description
                else []
            )

            return pd.DataFrame(
                rows,
                columns=cols
            )

        finally:

            cursor.close()

    def get_databases(self):

        cursor = self.conn.cursor()

        cursor.execute(
            "SHOW DATABASES"
        )

        rows = cursor.fetchall()

        cursor.close()

        return [r[1] for r in rows]

    def get_schemas(
        self,
        database
    ):

        sql = f"""
        SELECT SCHEMA_NAME
        FROM {database}.INFORMATION_SCHEMA.SCHEMATA
        ORDER BY SCHEMA_NAME
        """

        return self.execute(
            sql
        )["SCHEMA_NAME"].tolist()

    def get_tables(
        self,
        database,
        schema
    ):

        sql = f"""
        SELECT TABLE_NAME
        FROM {database}.INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA='{schema}'
        ORDER BY TABLE_NAME
        """

        return self.execute(
            sql
        )["TABLE_NAME"].tolist()

    def get_columns(
        self,
        database,
        schema,
        table
    ):

        sql = f"""
        SELECT
            COLUMN_NAME,
            DATA_TYPE
        FROM
        {database}.INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA='{schema}'
        AND TABLE_NAME='{table}'
        ORDER BY ORDINAL_POSITION
        """

        return self.execute(sql)

    def get_primary_keys(
        self,
        database,
        schema,
        table
    ):

        sql = f"""
        SHOW PRIMARY KEYS IN TABLE
        {database}.{schema}.{table}
        """

        return self.execute(sql)

    def get_relationships(
        self,
        database
    ):

        sql = f"""
        SELECT
            CONSTRAINT_NAME,
            TABLE_NAME,
            UNIQUE_CONSTRAINT_NAME
        FROM
        {database}.INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS
        """

        return self.execute(sql)