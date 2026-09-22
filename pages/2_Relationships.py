import streamlit as st

st.title("Relationship Builder")

if st.session_state.snowflake is None:
    st.warning("Please connect first.")
    st.stop()

if not st.session_state.datasets:
    st.warning("Configure datasets first.")
    st.stop()

##################################################
# TABLES
##################################################

tables = []

for ds in st.session_state.datasets:
    tables.append(ds["name"])

##################################################
# REL COUNT
##################################################

relationship_count = st.number_input(
    "Number Of Relationships",
    min_value=0,
    value=0,
    step=1
)

relationships = []

##################################################
# BUILDER
##################################################

for idx in range(relationship_count):

    st.divider()

    st.subheader(
        f"Relationship {idx + 1}"
    )

    col1, col2 = st.columns(2)

    ##################################################
    # FROM
    ##################################################

    with col1:

        from_table = st.selectbox(
            "From Table",
            tables,
            key=f"from_table_{idx}"
        )

        from_cols = []

        for ds in st.session_state.datasets:

            if ds["name"] == from_table:

                from_cols = [
                    f["name"]
                    for f in ds["fields"]
                ]

        from_column = st.selectbox(
            "From Column",
            from_cols,
            key=f"from_col_{idx}"
        )

    ##################################################
    # TO
    ##################################################

    with col2:

        to_table = st.selectbox(
            "To Table",
            tables,
            key=f"to_table_{idx}"
        )

        to_cols = []

        for ds in st.session_state.datasets:

            if ds["name"] == to_table:

                to_cols = [
                    f["name"]
                    for f in ds["fields"]
                ]

        to_column = st.selectbox(
            "To Column",
            to_cols,
            key=f"to_col_{idx}"
        )

    ##################################################
    # RELATIONSHIP OBJECT
    ##################################################

    relationship = {
        "name": f"{from_table}_TO_{to_table}",
        "from": from_table,
        "to": to_table,
        "from_columns": [
            from_column
        ],
        "to_columns": [
            to_column
        ]
    }

    relationships.append(
        relationship
    )

##################################################
# SAVE
##################################################

st.session_state.relationships = relationships

st.success(
    f"{len(relationships)} relationship(s) configured"
)

##################################################
# PREVIEW
##################################################

st.subheader(
    "Relationship Preview"
)

st.json(
    relationships
)