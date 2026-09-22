import streamlit as st

st.title("Metric Builder")

if st.session_state.snowflake is None:
    st.warning("Please connect first.")
    st.stop()

if not st.session_state.datasets:
    st.warning("Please configure datasets first.")
    st.stop()

#################################################
# METRIC COUNT
#################################################

metric_count = st.number_input(
    "Number of Metrics",
    min_value=0,
    value=1,
    step=1
)

metrics = []

#################################################
# METRICS
#################################################

for idx in range(metric_count):

    st.divider()

    st.subheader(
        f"Metric {idx + 1}"
    )

    metric_name = st.text_input(
        "Metric Name",
        key=f"metric_name_{idx}"
    )

    metric_description = st.text_input(
        "Description",
        key=f"metric_desc_{idx}"
    )

    metric_type = st.selectbox(
        "Metric Type",
        [
            "SUM",
            "AVG",
            "COUNT",
            "COUNT DISTINCT",
            "MIN",
            "MAX",
            "CUSTOM"
        ],
        key=f"metric_type_{idx}"
    )

    #################################################
    # STANDARD METRICS
    #################################################

    if metric_type != "CUSTOM":

        table = st.selectbox(
            "Dataset",
            [x["name"] for x in st.session_state.datasets],
            key=f"metric_table_{idx}"
        )

        cols = []

        for ds in st.session_state.datasets:

            if ds["name"] == table:

                cols = [
                    f["name"]
                    for f in ds["fields"]
                ]

        column = st.selectbox(
            "Column",
            cols,
            key=f"metric_col_{idx}"
        )

        if metric_type == "COUNT DISTINCT":

            expression = (
                f"COUNT(DISTINCT {table}.{column})"
            )

        else:

            expression = (
                f"{metric_type}({table}.{column})"
            )

        st.code(expression)

    #################################################
    # CUSTOM METRICS
    #################################################

    else:

        expression = st.text_area(
            "Custom Expression",
            key=f"custom_exp_{idx}",
            height=120
        )

    #################################################
    # BUILD JSON
    #################################################

    metric = {

        "name": metric_name,

        "expression": {
            "dialects": [
                {
                    "dialect": "SNOWFLAKE",
                    "expression": expression
                }
            ]
        },

        "description": metric_description,

        "custom_extensions": [
            {
                "vendor_name": "SNOWFLAKE",
                "data": "{\"access_modifier\":\"public_access\"}"
            }
        ]
    }

    metrics.append(metric)

#################################################
# SAVE
#################################################

st.session_state.metrics = metrics

st.success(
    f"{len(metrics)} metric(s) configured"
)

st.subheader("Metric Preview")

st.json(metrics)
