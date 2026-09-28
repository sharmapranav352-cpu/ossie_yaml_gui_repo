import streamlit as st

from services.builders import METRIC_TYPES
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
    "Add business metrics",
    "Define the numbers people ask about, like total revenue or active "
    "customers. Pick an aggregation, or choose CUSTOM to write an expression."
)

datasets_cfg = st.session_state.saved["datasets"]
saved_metrics = st.session_state.saved["metrics"]

if not datasets_cfg["tables"]:
    st.info("Save at least one dataset first. Metrics are built from saved datasets.")
    continue_to("datasets", "Go to datasets", full_width=False)
    st.stop()

tables = [t["name"] for t in datasets_cfg["tables"]]
columns_by_table = {
    t["name"]: t["selected_columns"] for t in datasets_cfg["tables"]
}

ids, seeds = row_ids("met_", saved_metrics)

metrics = []

#################################################
# ONE ROW PER METRIC
#################################################

# Column layout shared by the header row and every metric row
LAYOUT = [1.5, 0.85, 1.85, 1.8, 0.32]

with st.container(border=True):

    if ids:
        head = st.columns(LAYOUT, vertical_alignment="bottom")
        for col, label in zip(head, ["Name", "Aggregation", "Calculation",
                                     "Description", ""]):
            col.markdown(f"**{label}**" if label else "")

    for rid in ids:
        prev = seeds.get(rid, {})
        row = st.columns(LAYOUT, vertical_alignment="center")

        seed_value(f"met_{rid}_name", prev.get("name", ""))
        metric_name = row[0].text_input(
            "Name", key=f"met_{rid}_name", placeholder="TOTAL_REVENUE",
            label_visibility="collapsed",
        )

        seed_choice(f"met_{rid}_type", METRIC_TYPES, prev.get("type", "SUM"))
        metric_type = row[1].selectbox(
            "Aggregation", METRIC_TYPES, key=f"met_{rid}_type",
            label_visibility="collapsed",
        )

        metric = {
            "name": metric_name.strip(),
            "description": "",
            "type": metric_type,
            "table": None,
            "column": None,
            "expression": "",
        }

        if metric_type == "CUSTOM":
            seed_value(f"met_{rid}_custom", prev.get("expression", ""))
            metric["expression"] = row[2].text_input(
                "Expression",
                key=f"met_{rid}_custom",
                placeholder="TOTAL_PRICE / TOTAL_QUANTITY",
                label_visibility="collapsed",
                help="Any Snowflake SQL expression. It can refer to other metrics by name.",
            )
        else:
            src = row[2].columns(2)
            seed_choice(f"met_{rid}_table", tables, prev.get("table"))
            table = src[0].selectbox(
                "Dataset", tables, key=f"met_{rid}_table",
                label_visibility="collapsed",
            )

            cols = columns_by_table.get(table, [])
            seed_choice(f"met_{rid}_col", cols, prev.get("column"))
            column = src[1].selectbox(
                "Column", cols, key=f"met_{rid}_col",
                label_visibility="collapsed",
                help=f"Calculates {metric_type}({table}.<column>)",
            )

            metric["table"] = table
            metric["column"] = column

        seed_value(f"met_{rid}_desc", prev.get("description", ""))
        metric["description"] = row[3].text_input(
            "Description", key=f"met_{rid}_desc",
            placeholder="What this number means to the business",
            label_visibility="collapsed",
        ).strip()

        row[4].button(
            "", icon=":material/delete:", key=f"met_{rid}_del",
            help="Remove this metric",
            on_click=delete_row, args=("met_", rid),
        )

        metrics.append(metric)

    if not ids:
        st.markdown(
            '<p class="cx-hint">No metrics yet.</p>', unsafe_allow_html=True
        )

    st.button(
        "Add metric", icon=":material/add:", key="met_add",
        on_click=add_row, args=("met_",),
    )

st.caption(
    "Choose CUSTOM to write your own expression, for example one metric "
    "divided by another."
)

#################################################
# CHECKS AND SAVE
#################################################

names = [m["name"] for m in metrics if m["name"]]
dupes = sorted({n for n in names if names.count(n) > 1})
if dupes:
    st.error("Duplicate metric names: " + ", ".join(dupes))

if any(not m["name"] for m in metrics):
    st.info("Every metric needs a name before it can be published.")

save_bar(
    "Save metrics",
    metrics,
    saved_metrics,
    lambda cfg: (
        save_section("metrics", cfg),
        # cards restore from what was just saved when you come back to this page
        st.session_state.__setitem__("met_seed", dict(zip(ids, cfg))),
    ),
    next_step=("publish", "Continue to publish"),
)
