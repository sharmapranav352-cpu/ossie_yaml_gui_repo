import streamlit as st

st.title("Dataset Builder")

if st.session_state.snowflake is None:

    st.warning(
        "Please connect to Snowflake first."
    )

    st.stop()

sf = st.session_state.snowflake

##################################################
# DATABASE
##################################################

databases = sf.get_databases()

database = st.selectbox(
    "Database",
    databases
)

##################################################
# SCHEMA
##################################################

schemas = sf.get_schemas(
    database
)

schema = st.selectbox(
    "Schema",
    schemas
)

##################################################
# TABLES
##################################################

tables = sf.get_tables(
    database,
    schema
)

selected_tables = st.multiselect(
    "Select Tables",
    tables
)

##################################################
# DATASETS
##################################################

datasets = []

st.divider()

for table in selected_tables:

    with st.expander(
        f"Dataset: {table}",
        expanded=True
    ):

        columns_df = sf.get_columns(
            database,
            schema,
            table
        )

        available_columns = (
            columns_df["COLUMN_NAME"]
            .tolist()
        )

        selected_columns = st.multiselect(
            f"Columns - {table}",
            available_columns,
            default=available_columns,
            key=f"{table}_columns"
        )

        primary_keys = st.multiselect(
            f"Primary Keys - {table}",
            selected_columns,
            key=f"{table}_pk"
        )

        time_columns = st.multiselect(
            f"Time Dimensions - {table}",
            selected_columns,
            key=f"{table}_time"
        )

        fields = []

        for col in selected_columns:

            field = {
                "name": col,

                "expression": {
                    "dialects": [
                        {
                            "dialect":
                            "SNOWFLAKE",

                            "expression":
                            col
                        }
                    ]
                },

                "custom_extensions": [
                    {
                        "vendor_name":
                        "SNOWFLAKE",

                        "data":
                        "{\"access_modifier\":\"public_access\"}"
                    }
                ]
            }

            if col in time_columns:

                field["dimension"] = {
                    "is_time": True
                }

            else:

                field["dimension"] = {}

            fields.append(field)

        dataset = {
            "name": table,

            "source":
            f"{database}.{schema}.{table}",

            "fields":
            fields
        }

        if primary_keys:

            dataset["primary_key"] = (
                primary_keys
            )

        datasets.append(
            dataset
        )

##################################################
# SAVE
##################################################

st.session_state.datasets = datasets

st.success(
    f"{len(datasets)} datasets configured"
)

with st.expander(
    "Current Dataset JSON"
):

    st.json(
        st.session_state.datasets
    )