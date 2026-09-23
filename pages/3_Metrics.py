import streamlit as st

from services.builders import METRIC_TYPES, build_metrics, metric_expression
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
    "Add business metrics",
    "Define the numbers people ask about, like total revenue or active "
    "customers. Pick an aggregation or write your own expression."
)

datasets_cfg = st.session_state.saved["datasets"]
saved_metrics = st.session_state.saved["metrics"]

if not datasets_cfg["tables"]:
    st.info("Save at least one dataset first. Metrics are built from saved datasets.")
    continue_to("datasets", "Go to datasets")
    st.stop()

tables = [t["name"] for t in datasets_cfg["tables"]]
columns_by_table = {
    t["name"]: t["selected_columns"] for t in datasets_cfg["tables"]
}

#################################################
# METRIC COUNT
#################################################

seed_value("met_count", len(saved_metrics))

metric_count = st.columns([1, 3])[0].number_input(
    "Number of metrics",
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

    box = st.container(border=True)
    box.markdown(f"**Metric {idx + 1}**")

    n1, n2 = box.columns([1, 2])

    seed_value(f"met_{idx}_name", prev.get("name", ""))
    metric_name = n1.text_input(
        "Name", key=f"met_{idx}_name", placeholder="TOTAL_REVENUE"
    )

    seed_value(f"met_{idx}_desc", prev.get("description", ""))
    metric_description = n2.text_input(
        "Description", key=f"met_{idx}_desc",
        placeholder="What this number means to the business"
    )

    t1, t2, t3 = box.columns(3)

    seed_choice(f"met_{idx}_type", METRIC_TYPES, prev.get("type", "SUM"))
    metric_type = t1.selectbox(
        "Aggregation", METRIC_TYPES, key=f"met_{idx}_type"
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
        table = t2.selectbox(
            "Dataset", tables, key=f"met_{idx}_table"
        )

        cols = columns_by_table.get(table, [])
        seed_choice(f"met_{idx}_col", cols, prev.get("column"))
        column = t3.selectbox("Column", cols, key=f"met_{idx}_col")

        metric["table"] = table
        metric["column"] = column

    else:

        seed_value(f"met_{idx}_custom", prev.get("expression", ""))
        metric["expression"] = box.text_area(
            "Expression",
            key=f"met_{idx}_custom",
            height=120,
            help="You can reference other metrics, e.g. TOTAL_PRICE / TOTAL_QUANTITY"
        )

    box.code(metric_expression(metric) or "-- enter an expression --", language="sql")

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
    "Save metrics",
    metrics,
    saved_metrics,
    lambda cfg: save_section("metrics", cfg),
    next_step=("generate", "Continue to generate")
)

with st.expander("View saved metrics as JSON"):
    st.json(build_metrics(st.session_state.saved["metrics"]), expanded=False)
