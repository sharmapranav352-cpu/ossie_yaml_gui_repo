import streamlit as st

from services.builders import build_relationships, relationship_name
from utils.branding import continue_to, page_header
from utils.state import (
    init_state,
    save_bar,
    save_section,
    seed_choice,
    seed_value,
)

init_state()

page_header(
    "Define relationships",
    "Tell the model how your datasets join, for example orders to "
    "customers on the customer key."
)

datasets_cfg = st.session_state.saved["datasets"]
saved_rels = st.session_state.saved["relationships"]

if not datasets_cfg["tables"]:
    st.info("Save at least one dataset first. Relationships are built from saved datasets.")
    continue_to("datasets", "Go to datasets")
    st.stop()

tables = [t["name"] for t in datasets_cfg["tables"]]
columns_by_table = {
    t["name"]: t["selected_columns"] for t in datasets_cfg["tables"]
}

st.caption(
    "Tables and columns come from your saved datasets. "
    "If one is missing, add it on the Datasets page and save again."
)

##################################################
# REL COUNT
##################################################

seed_value("rel_count", len(saved_rels))

relationship_count = st.columns([1, 3])[0].number_input(
    "Number of relationships",
    min_value=0,
    step=1,
    key="rel_count"
)

relationships = []

##################################################
# BUILDER
##################################################

for idx in range(int(relationship_count)):

    prev = saved_rels[idx] if idx < len(saved_rels) else {}

    box = st.container(border=True)
    box.markdown(f"**Relationship {idx + 1}**")

    col1, col2 = box.columns(2)

    with col1:

        seed_choice(f"rel_{idx}_from_table", tables, prev.get("from_table"))
        from_table = st.selectbox(
            "From table", tables, key=f"rel_{idx}_from_table"
        )

        from_cols = columns_by_table.get(from_table, [])
        seed_choice(f"rel_{idx}_from_col", from_cols, prev.get("from_column"))
        from_column = st.selectbox(
            "Join column", from_cols, key=f"rel_{idx}_from_col"
        )

    with col2:

        seed_choice(f"rel_{idx}_to_table", tables, prev.get("to_table"))
        to_table = st.selectbox(
            "To table", tables, key=f"rel_{idx}_to_table"
        )

        to_cols = columns_by_table.get(to_table, [])
        seed_choice(f"rel_{idx}_to_col", to_cols, prev.get("to_column"))
        to_column = st.selectbox(
            "Join column", to_cols, key=f"rel_{idx}_to_col"
        )

    seed_value(f"rel_{idx}_name", prev.get("name", ""))
    custom_name = box.text_input(
        "Name (optional)",
        key=f"rel_{idx}_name",
        placeholder=f"{from_table}_TO_{to_table}"
    )

    if from_table == to_table:
        box.warning("This relationship joins a table to itself.")

    relationships.append({
        "name": custom_name.strip(),
        "from_table": from_table,
        "from_column": from_column,
        "to_table": to_table,
        "to_column": to_column,
    })

##################################################
# SAVE
##################################################

st.divider()

names = [relationship_name(r) for r in relationships]
dupes = sorted({n for n in names if names.count(n) > 1})
if dupes:
    st.error(
        "Duplicate relationship names: " + ", ".join(dupes)
        + ". Give them custom names."
    )

save_bar(
    "Save relationships",
    relationships,
    saved_rels,
    lambda cfg: save_section("relationships", cfg),
    next_step=("metrics", "Continue to metrics")
)

with st.expander("View saved relationships as JSON"):
    st.json(
        build_relationships(st.session_state.saved["relationships"]),
        expanded=False
    )
