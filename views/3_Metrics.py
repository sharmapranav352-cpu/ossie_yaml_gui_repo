import streamlit as st

from services.builders import METRIC_TYPES
from services.ossie_import import _AGG
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


def _match(options, value):
    """The option equal to value, ignoring upper/lower case; None if there isn't one."""
    if value in options:
        return value
    lowered = {o.lower(): o for o in options}
    return lowered.get((value or "").lower())


def seed_source(rid, prev):
    """
    Pick the dataset and column for a SUM/AVG/... metric without guessing.
    Uses the saved values, or the table.column inside the metric's current
    expression (e.g. SUM(orders.o_totalprice) -> ORDERS / O_TOTALPRICE).
    Anything that doesn't match stays empty for the user to choose.
    """
    t_key, c_key = f"met_{rid}_table", f"met_{rid}_col"

    if t_key not in st.session_state:
        table, column = prev.get("table"), prev.get("column")
        expr = st.session_state.get(f"met_{rid}_custom") or prev.get("expression") or ""
        found = _AGG.match(expr)
        if found and not table:
            table, column = found.group(3), found.group(4)
        st.session_state[t_key] = _match(tables, table)
        st.session_state[c_key] = column   # checked against the table's columns below
    elif st.session_state[t_key] not in tables:
        st.session_state[t_key] = None

    cols = columns_by_table.get(st.session_state[t_key], [])
    st.session_state[c_key] = _match(cols, st.session_state.get(c_key))
    return cols


metrics = []

#################################################
# ONE ROW PER METRIC
#################################################

# Column layout shared by the header row and every metric row
LAYOUT = [1.45, 0.82, 1.8, 1.7, 0.6, 0.3]

with st.container(border=True):

    if ids:
        head = st.columns(LAYOUT, vertical_alignment="bottom")
        for col, label in zip(head, ["Name", "Aggregation", "Calculation",
                                     "Description", "Add Dialect", ""]):
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
            cols = seed_source(rid, prev)
            table = src[0].selectbox(
                "Dataset", tables, key=f"met_{rid}_table",
                label_visibility="collapsed", placeholder="Choose dataset",
            )
            cols = columns_by_table.get(table, [])
            column = src[1].selectbox(
                "Column", cols, key=f"met_{rid}_col",
                label_visibility="collapsed", placeholder="Choose column",
                help=f"Calculates {metric_type}({table or 'dataset'}.<column>)",
            )

            metric["table"] = table
            metric["column"] = column
            # Remember the custom expression in case this goes back to CUSTOM
            # (it is only written to the YAML for CUSTOM metrics)
            metric["expression"] = prev.get("expression", "")

        seed_value(f"met_{rid}_desc", prev.get("description", ""))
        metric["description"] = row[3].text_input(
            "Description", key=f"met_{rid}_desc",
            placeholder="What this number means to the business",
            label_visibility="collapsed",
        ).strip()

        # "Add Dialect": a second expression for Power BI / Fabric, always DAX
        seed_value(f"met_{rid}_add_dax", bool(prev.get("add_dax")))
        add_dax = row[4].checkbox(
            "DAX", key=f"met_{rid}_add_dax",
            help="Add a DAX expression for this metric. It is written to the "
                 "YAML as a second dialect, after SNOWFLAKE.",
        )

        row[5].button(
            "", icon=":material/delete:", key=f"met_{rid}_del",
            help="Remove this metric",
            on_click=delete_row, args=("met_", rid),
        )

        metric["add_dax"] = add_dax
        metric["dax_expression"] = prev.get("dax_expression", "")

        if add_dax:
            # DAX box under the row, spanning Aggregation, Calculation and Description
            dax_row = st.columns(
                [LAYOUT[0], LAYOUT[1] + LAYOUT[2] + LAYOUT[3], LAYOUT[4] + LAYOUT[5]],
                vertical_alignment="center",
            )
            dax_row[0].markdown(
                "<div style='text-align:right;color:#5A6878;font-size:.875rem;"
                "font-weight:600;padding-right:.25rem'>DAX</div>",
                unsafe_allow_html=True,
            )
            seed_value(f"met_{rid}_dax", prev.get("dax_expression", ""))
            metric["dax_expression"] = dax_row[1].text_input(
                "DAX expression", key=f"met_{rid}_dax",
                placeholder="DIVIDE([TOTAL_PRICE], [TOTAL_QUANTITY])",
                label_visibility="collapsed",
            ).strip()

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
    "divided by another. Tick Add Dialect to add a DAX expression for "
    "Power BI / Fabric."
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
    back_step="relationships",
)
