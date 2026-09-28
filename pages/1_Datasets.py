import pandas as pd
import streamlit as st

from services.builders import TIME_TYPES
from utils.branding import continue_to, page_header
from utils.state import (
    cached_meta,
    clear_meta_cache,
    init_state,
    save_bar,
    save_section,
    seed_choice,
    seed_multi,
)

init_state()

page_header(
    "Choose your datasets",
    "Select the Snowflake tables to include, then choose the columns, key, "
    "date fields and facts for each one."
)

saved_cfg = st.session_state.saved["datasets"]
sf = st.session_state.snowflake


def _summary(tables):
    return pd.DataFrame([
        {
            "Dataset": t["name"],
            "Source": t["source"],
            "Columns": len(t["selected_columns"]),
            "Primary key": ", ".join(t["primary_keys"]) or "None",
            "Facts": ", ".join(t.get("fact_columns", [])) or "None",
        }
        for t in tables
    ])


##################################################
# NOT CONNECTED: SHOW WHAT IS SAVED
##################################################

if sf is None:

    st.info("Connect to Snowflake to choose or edit datasets.")

    if saved_cfg["tables"]:
        st.markdown(
            f'<p class="cx-section">Saved datasets from '
            f'{saved_cfg["database"]}.{saved_cfg["schema"]}</p>',
            unsafe_allow_html=True,
        )
        st.dataframe(_summary(saved_cfg["tables"]), hide_index=True,
                     width="stretch")

    continue_to("connect", "Go to connect", full_width=False)
    st.stop()

##################################################
# SOURCE: DATABASE, SCHEMA, TABLES
##################################################

with st.container(border=True):

    databases = cached_meta("databases", sf.get_databases)
    seed_choice("ds_database", databases, saved_cfg["database"])

    src1, src2, src3 = st.columns([2, 2, 1], vertical_alignment="bottom")

    database = src1.selectbox("Database", databases, key="ds_database")

    schemas = cached_meta("schemas", sf.get_schemas, database) if database else []
    seed_choice(
        "ds_schema",
        schemas,
        saved_cfg["schema"] if database == saved_cfg["database"] else None,
    )
    schema = src2.selectbox("Schema", schemas, key="ds_schema")

    if src3.button(
        "Refresh",
        icon=":material/refresh:",
        width="stretch",
        help="Reload databases, schemas, tables and columns from Snowflake.",
    ):
        clear_meta_cache()
        st.rerun()

    tables = (
        cached_meta("tables", sf.get_tables, database, schema)
        if database and schema else []
    )

    same_scope = (
        database == saved_cfg["database"] and schema == saved_cfg["schema"]
    )
    saved_tables = {t["name"]: t for t in saved_cfg["tables"]} if same_scope else {}

    seed_multi("ds_tables", tables, list(saved_tables))
    selected_tables = st.multiselect(
        "Tables", tables, key="ds_tables",
        placeholder="Choose the tables to include",
    )


def suggested_primary_keys(table):
    """Declared primary keys from Snowflake, if any."""
    try:
        df = cached_meta("pks", sf.get_primary_keys, database, schema, table)
        return df["column_name"].tolist() if "column_name" in df else []
    except Exception:
        return []


##################################################
# ONE PANEL PER TABLE
##################################################

if not selected_tables:
    st.markdown(
        '<p class="cx-hint">Choose one or more tables above to set them up '
        'as datasets.</p>',
        unsafe_allow_html=True,
    )

table_cfgs = []

for table in selected_tables:

    prev = saved_tables.get(table)
    key = f"ds_{database}.{schema}.{table}"

    columns_df = cached_meta("columns", sf.get_columns, database, schema, table)
    available = columns_df["COLUMN_NAME"].tolist()
    types = dict(zip(columns_df["COLUMN_NAME"], columns_df["DATA_TYPE"]))

    n_selected = len(st.session_state.get(
        f"{key}.cols", prev["selected_columns"] if prev else available
    ))
    n_facts = len(st.session_state.get(
        f"{key}.facts", prev.get("fact_columns", []) if prev else []
    ))
    summary = f"{n_selected} of {len(available)} columns"
    if n_facts:
        summary += f", {n_facts} fact{'' if n_facts == 1 else 's'}"

    with st.expander(f"**{table}**  \n{summary}", expanded=len(selected_tables) == 1):

        seed_multi(f"{key}.cols", available,
                   prev["selected_columns"] if prev else available)
        selected_columns = st.multiselect("Columns", available, key=f"{key}.cols")

        c1, c2, c3 = st.columns(3)

        seed_multi(f"{key}.pk", selected_columns,
                   prev["primary_keys"] if prev else suggested_primary_keys(table))
        primary_keys = c1.multiselect(
            "Primary key", selected_columns, key=f"{key}.pk",
            placeholder="None",
        )

        seed_multi(
            f"{key}.time", selected_columns,
            prev["time_columns"] if prev else [
                c for c in selected_columns if types.get(c, "").upper() in TIME_TYPES
            ],
        )
        time_columns = c2.multiselect(
            "Date and time fields", selected_columns, key=f"{key}.time",
            placeholder="None",
            help="Date and timestamp columns are selected for you.",
        )

        fact_options = [c for c in selected_columns if c not in time_columns]
        seed_multi(f"{key}.facts", fact_options,
                   prev.get("fact_columns", []) if prev else [])
        fact_columns = c3.multiselect(
            "Facts (measures)", fact_options, key=f"{key}.facts",
            placeholder="None",
            help=(
                "Numeric values you add up or average, such as prices and "
                "quantities. Every other column is a dimension you group or "
                "filter by."
            ),
        )

    table_cfgs.append({
        "name": table,
        "source": f"{database}.{schema}.{table}",
        "selected_columns": selected_columns,
        "primary_keys": primary_keys,
        "time_columns": time_columns,
        "fact_columns": fact_columns,
    })

##################################################
# SAVE
##################################################

current = {"database": database, "schema": schema, "tables": table_cfgs}

latest = st.session_state.saved["datasets"]
if latest["tables"] and (
    latest["database"] != database or latest["schema"] != schema
):
    st.warning(
        f"You have {len(latest['tables'])} dataset(s) saved from "
        f"{latest['database']}.{latest['schema']}. Saving here replaces them."
    )

has_work = bool(saved_cfg["tables"] or table_cfgs)

save_bar(
    "Save datasets",
    current,
    saved_cfg if has_work else current,
    lambda cfg: save_section("datasets", cfg),
    next_step=("relationships", "Continue to relationships") if has_work else None,
    back_step="connect",
)
