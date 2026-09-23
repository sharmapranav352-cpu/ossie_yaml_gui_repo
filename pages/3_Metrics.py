import streamlit as st

from services.builders import METRIC_TYPES, build_metrics, metric_expression
from utils.state import (
    init_state,
    save_bar,
    save_section,
    seed_choice,
    seed_value,
)

st.title("Metric Builder")

init_state()

datasets_cfg = st.session_state.saved["datasets"]
saved_metrics = st.session_state.saved["metrics"]

if not datasets_cfg["tables"]:
    st.warning("Save at least one dataset on the Datasets page first.")
    st.stop()

tables = [t["name"] for t in datasets_cfg["tables"]]
columns_by_table = {
    t["name"]: t["selected_columns"] for t in datasets_cfg["tables"]
}

#################################################
# METRIC COUNT
#################################################

seed_value("met_count", len(saved_metrics))

metric_count = st.number_input(
    "Number of Metrics",
    min_value=0,
    step=1,
    key="met_count"
)

metrics = []

#################################################
# METRICS
#################################################

for idx in range(int(metric_count)):

    prev = saved_metrics[idx] if idx < len(saved_metrics) else {}

    st.divider()
    st.subheader(f"Metric {idx + 1}")

    seed_value(f"met_{idx}_name", prev.get("name", ""))
    metric_name = st.text_input("Metric Name", key=f"met_{idx}_name")

    seed_value(f"met_{idx}_desc", prev.get("description", ""))
    metric_description = st.text_input(
        "Description", key=f"met_{idx}_desc"
    )

    seed_choice(f"met_{idx}_type", METRIC_TYPES, prev.get("type", "SUM"))
    metric_type = st.selectbox(
        "Metric Type", METRIC_TYPES, key=f"met_{idx}_type"
    )

    metric = {
        "name": metric_name.strip(),
        "description": metric_description.strip(),
        "type": metric_type,
        "table": None,
        "column": None,
        "expression": "",
    }

    if metric_type != "CUSTOM":

        seed_choice(f"met_{idx}_table", tables, prev.get("table"))
        table = st.selectbox(
            "Dataset", tables, key=f"met_{idx}_table"
        )

        cols = columns_by_table.get(table, [])
        seed_choice(f"met_{idx}_col", cols, prev.get("column"))
        column = st.selectbox("Column", cols, key=f"met_{idx}_col")

        metric["table"] = table
        metric["column"] = column

    else:

        seed_value(f"met_{idx}_custom", prev.get("expression", ""))
        metric["expression"] = st.text_area(
            "Custom Expression",
            key=f"met_{idx}_custom",
            height=120,
            help="You can reference other metrics, e.g. TOTAL_PRICE / TOTAL_QUANTITY"
        )

    st.code(metric_expression(metric) or "-- empty --", language="sql")

    metrics.append(metric)

#################################################
# SAVE
#################################################

st.divider()

names = [m["name"] for m in metrics if m["name"]]
dupes = sorted({n for n in names if names.count(n) > 1})
if dupes:
    st.error("Duplicate metric names: " + ", ".join(dupes))

if any(not m["name"] for m in metrics):
    st.info("Every metric needs a name before the YAML can be generated.")

save_bar(
    "💾 Save Metrics",
    metrics,
    saved_metrics,
    lambda cfg: save_section("metrics", cfg)
)

with st.expander("Saved Metric JSON"):
    st.json(build_metrics(st.session_state.saved["metrics"]))
