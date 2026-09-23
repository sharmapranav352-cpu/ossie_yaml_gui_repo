import streamlit as st

from services.builders import TIME_TYPES, build_datasets
from utils.state import (
    cached_meta,
    clear_meta_cache,
    init_state,
    save_bar,
    save_section,
    seed_choice,
    seed_multi,
)

st.title("Dataset Builder")

init_state()

saved_cfg = st.session_state.saved["datasets"]
sf = st.session_state.snowflake

##################################################
# NOT CONNECTED: SHOW WHAT IS SAVED
##################################################

if sf is None:

    st.warning(
        "Connect to Snowflake on the app page to edit datasets."
    )

    if saved_cfg["tables"]:
        st.info(
            f"Saved: {len(saved_cfg['tables'])} dataset(s) from "
            f"{saved_cfg['database']}.{saved_cfg['schema']}"
        )
        with st.expander("Saved datasets"):
            st.json(build_datasets(saved_cfg))

    st.stop()

if st.button("↻ Refresh Snowflake metadata"):
    clear_meta_cache()

##################################################
# DATABASE / SCHEMA
##################################################

databases = cached_meta("databases", sf.get_databases)

seed_choice("ds_database", databases, saved_cfg["database"])

database = st.selectbox(
    "Database",
    databases,
    key="ds_database"
)

schemas = (
    cached_meta("schemas", sf.get_schemas, database)
    if database else []
)

seed_choice(
    "ds_schema",
    schemas,
    saved_cfg["schema"] if database == saved_cfg["database"] else None
)

schema = st.selectbox(
    "Schema",
    schemas,
    key="ds_schema"
)

##################################################
# TABLES
##################################################

tables = (
    cached_meta("tables", sf.get_tables, database, schema)
    if database and schema else []
)

same_scope = (
    database == saved_cfg["database"]
    and schema == saved_cfg["schema"]
)

saved_tables = (
    {t["name"]: t for t in saved_cfg["tables"]}
    if same_scope else {}
)

seed_multi("ds_tables", tables, list(saved_tables))

selected_tables = st.multiselect(
    "Select Tables",
    tables,
    key="ds_tables"
)


def suggested_primary_keys(table):
    """Declared primary keys from Snowflake, if any."""
    try:
        df = cached_meta(
            "pks", sf.get_primary_keys, database, schema, table
        )
        return df["column_name"].tolist() if "column_name" in df else []
    except Exception:
        return []


##################################################
# PER-TABLE CONFIG
##################################################

st.divider()

table_cfgs = []

for table in selected_tables:

    prev = saved_tables.get(table)
    key = f"ds_{database}.{schema}.{table}"

    with st.expander(f"Dataset: {table}", expanded=True):

        columns_df = cached_meta(
            "columns", sf.get_columns, database, schema, table
        )

        available = columns_df["COLUMN_NAME"].tolist()
        types = dict(
            zip(columns_df["COLUMN_NAME"], columns_df["DATA_TYPE"])
        )

        seed_multi(
            f"{key}.cols",
            available,
            prev["selected_columns"] if prev else available
        )

        selected_columns = st.multiselect(
            f"Columns - {table}",
            available,
            key=f"{key}.cols"
        )

        seed_multi(
            f"{key}.pk",
            selected_columns,
            prev["primary_keys"] if prev
            else suggested_primary_keys(table)
        )

        primary_keys = st.multiselect(
            f"Primary Keys - {table}",
            selected_columns,
            key=f"{key}.pk"
        )

        seed_multi(
            f"{key}.time",
            selected_columns,
            prev["time_columns"] if prev else [
                c for c in selected_columns
                if types.get(c, "").upper() in TIME_TYPES
            ]
        )

        time_columns = st.multiselect(
            f"Time Dimensions - {table}",
            selected_columns,
            key=f"{key}.time",
            help="Date/timestamp columns are pre-selected."
        )

    table_cfgs.append({
        "name": table,
        "source": f"{database}.{schema}.{table}",
        "selected_columns": selected_columns,
        "primary_keys": primary_keys,
        "time_columns": time_columns,
        "column_types": {c: types.get(c) for c in selected_columns},
    })

##################################################
# SAVE
##################################################

current = {
    "database": database,
    "schema": schema,
    "tables": table_cfgs,
}

st.divider()

save_bar(
    "💾 Save Datasets",
    current,
    saved_cfg,
    lambda cfg: save_section("datasets", cfg)
)

latest = st.session_state.saved["datasets"]

if latest["tables"] and (
    latest["database"] != database or latest["schema"] != schema
):
    st.caption(
        f"Currently saved: {len(latest['tables'])} dataset(s) from "
        f"{latest['database']}.{latest['schema']}. "
        "Saving here will replace them."
    )

with st.expander("Saved Dataset JSON"):
    st.json(build_datasets(latest))
