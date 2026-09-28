import streamlit as st

from services.builders import relationship_name
from utils.branding import continue_to, page_header
from utils.state import (
    add_row,
    delete_row,
    init_state,
    row_ids,
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
    continue_to("datasets", "Go to datasets", full_width=False)
    st.stop()

tables = [t["name"] for t in datasets_cfg["tables"]]
columns_by_table = {
    t["name"]: t["selected_columns"] for t in datasets_cfg["tables"]
}

ids, seeds = row_ids("rel_", saved_rels)

# Column layout shared by the header row and every relationship row
LAYOUT = [1.15, 1.15, 1.15, 1.15, 1.3, 0.32]

relationships = []

with st.container(border=True):

    if ids:
        head = st.columns(LAYOUT, vertical_alignment="bottom")
        for col, label in zip(head, ["From table", "Join column", "To table",
                                     "Join column", "Name", ""]):
            col.markdown(f"**{label}**" if label else "")

    for rid in ids:
        prev = seeds.get(rid, {})
        row = st.columns(LAYOUT, vertical_alignment="center")

        seed_choice(f"rel_{rid}_from_table", tables, prev.get("from_table"))
        from_table = row[0].selectbox(
            "From table", tables, key=f"rel_{rid}_from_table",
            label_visibility="collapsed",
        )

        from_cols = columns_by_table.get(from_table, [])
        seed_choice(f"rel_{rid}_from_col", from_cols, prev.get("from_column"))
        from_column = row[1].selectbox(
            "From column", from_cols, key=f"rel_{rid}_from_col",
            label_visibility="collapsed",
        )

        seed_choice(f"rel_{rid}_to_table", tables, prev.get("to_table"))
        to_table = row[2].selectbox(
            "To table", tables, key=f"rel_{rid}_to_table",
            label_visibility="collapsed",
        )

        to_cols = columns_by_table.get(to_table, [])
        seed_choice(f"rel_{rid}_to_col", to_cols, prev.get("to_column"))
        to_column = row[3].selectbox(
            "To column", to_cols, key=f"rel_{rid}_to_col",
            label_visibility="collapsed",
        )

        seed_value(f"rel_{rid}_name", prev.get("name", ""))
        custom_name = row[4].text_input(
            "Name", key=f"rel_{rid}_name",
            placeholder=f"{from_table}_TO_{to_table}",
            label_visibility="collapsed",
            help="Leave blank to use the name shown.",
        )

        row[5].button(
            "", icon=":material/delete:", key=f"rel_{rid}_del",
            help="Remove this relationship",
            on_click=delete_row, args=("rel_", rid),
        )

        relationships.append({
            "name": custom_name.strip(),
            "from_table": from_table,
            "from_column": from_column,
            "to_table": to_table,
            "to_column": to_column,
        })

    if not ids:
        st.markdown(
            '<p class="cx-hint">No relationships yet. Add one for each pair of '
            'datasets that join.</p>',
            unsafe_allow_html=True,
        )

    st.button(
        "Add relationship", icon=":material/add:", key="rel_add",
        on_click=add_row, args=("rel_",),
    )

st.caption(
    "Tables and columns come from your saved datasets. If one is missing, "
    "add it on the Datasets page and save again."
)

#################################################
# CHECKS AND SAVE
#################################################

self_joins = [
    relationship_name(r) for r in relationships if r["from_table"] == r["to_table"]
]
if self_joins:
    st.warning("Joins a table to itself: " + ", ".join(self_joins))

names = [relationship_name(r) for r in relationships]
dupes = sorted({n for n in names if names.count(n) > 1})
if dupes:
    st.error(
        "Duplicate relationship names: " + ", ".join(dupes)
        + ". Give them different names."
    )

save_bar(
    "Save relationships",
    relationships,
    saved_rels,
    lambda cfg: (
        save_section("relationships", cfg),
        # rows restore from what was just saved when you come back to this page
        st.session_state.__setitem__("rel_seed", dict(zip(ids, cfg))),
    ),
    next_step=("metrics", "Continue to metrics"),
)
