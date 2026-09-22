import snowflake.connector
import pandas as pd


class SnowflakeService:

    def __init__(
        self,
        account,
        username,
        password,
        warehouse,
        role
    ):

        self.conn = (
            snowflake.connector.connect(
                account=account,
                user=username,
                password=password,
                warehouse=warehouse,
                role=role
            )
        )

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
