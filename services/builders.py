"""
Turn the saved page configurations into OSSIE objects, and validate them.
"""

import copy

PUBLIC_ACCESS = [
    {
        "vendor_name": "SNOWFLAKE",
        "data": "{\"access_modifier\":\"public_access\"}",
    }
]

METRIC_TYPES = [
    "SUM",
    "AVG",
    "COUNT",
    "COUNT DISTINCT",
    "MIN",
    "MAX",
    "CUSTOM",
]

TIME_TYPES = (
    "DATE",
    "DATETIME",
    "TIME",
    "TIMESTAMP",
    "TIMESTAMP_LTZ",
    "TIMESTAMP_NTZ",
    "TIMESTAMP_TZ",
)


def _snowflake_expr(expression):
    return {
        "dialects": [
            {
                "dialect": "SNOWFLAKE",
                "expression": expression,
            }
        ]
    }


##################################################
# DATASETS
##################################################

def build_datasets(cfg):
    datasets = []

    for table in cfg.get("tables", []):
        fields = []

        for col in table["selected_columns"]:
            fields.append({
                "name": col,
                "expression": _snowflake_expr(col),
                "custom_extensions": copy.deepcopy(PUBLIC_ACCESS),
                "dimension": (
                    {"is_time": True}
                    if col in table["time_columns"]
                    else {}
                ),
            })

        dataset = {
            "name": table["name"],
            "source": table["source"],
            "fields": fields,
        }

        if table["primary_keys"]:
            dataset["primary_key"] = list(table["primary_keys"])

        datasets.append(dataset)

    return datasets


##################################################
# RELATIONSHIPS
##################################################

def relationship_name(rel):
    return rel.get("name") or f"{rel['from_table']}_TO_{rel['to_table']}"


def build_relationships(cfg):
    return [
        {
            "name": relationship_name(rel),
            "from": rel["from_table"],
            "to": rel["to_table"],
            "from_columns": [rel["from_column"]],
            "to_columns": [rel["to_column"]],
        }
        for rel in cfg
    ]


##################################################
# METRICS
##################################################

def metric_expression(metric):
    mtype = metric["type"]

    if mtype == "CUSTOM":
        return (metric.get("expression") or "").strip()

    ref = f"{metric['table']}.{metric['column']}"

    if mtype == "COUNT DISTINCT":
        return f"COUNT(DISTINCT {ref})"

    return f"{mtype}({ref})"


def build_metrics(cfg):
    return [
        {
            "name": metric["name"],
            "expression": _snowflake_expr(metric_expression(metric)),
            "description": metric.get("description", ""),
            "custom_extensions": copy.deepcopy(PUBLIC_ACCESS),
        }
        for metric in cfg
    ]


##################################################
# VALIDATION
##################################################

def validate(saved):
    """Return (errors, warnings). Errors block YAML generation."""
    errors = []
    warnings = []

    tables = saved["datasets"].get("tables", [])
    columns = {t["name"]: set(t["selected_columns"]) for t in tables}

    if not saved["model"].get("name", "").strip():
        errors.append("Semantic model name is empty.")

    # Datasets
    if not tables:
        errors.append("No datasets saved. Save them on the Datasets page.")

    for t in tables:
        if not t["selected_columns"]:
            errors.append(f"Dataset {t['name']} has no columns selected.")

    # Relationships
    rel_names = set()
    for i, rel in enumerate(saved["relationships"], start=1):
        label = f"Relationship {i}"

        for side in ("from", "to"):
            table = rel.get(f"{side}_table")
            column = rel.get(f"{side}_column")

            if table not in columns:
                errors.append(
                    f"{label}: table {table} is not a saved dataset."
                )
            elif column not in columns[table]:
                errors.append(
                    f"{label}: column {column} is not selected "
                    f"in dataset {table}."
                )

        if rel.get("from_table") == rel.get("to_table"):
            warnings.append(f"{label} joins a table to itself.")

        name = relationship_name(rel)
        if name in rel_names:
            errors.append(
                f"Duplicate relationship name {name}. "
                "Give one of them a custom name."
            )
        rel_names.add(name)

    # Metrics
    metric_names = set()
    for i, metric in enumerate(saved["metrics"], start=1):
        name = (metric.get("name") or "").strip()
        label = f"Metric {i}" + (f" ({name})" if name else "")

        if not name:
            errors.append(f"{label} has no name.")
        elif name in metric_names:
            errors.append(f"Duplicate metric name {name}.")
        elif " " in name:
            warnings.append(f"{label}: name contains spaces.")
        metric_names.add(name)

        if metric["type"] == "CUSTOM":
            if not metric_expression(metric):
                errors.append(f"{label} has an empty custom expression.")
        else:
            table = metric.get("table")
            if table not in columns:
                errors.append(
                    f"{label}: table {table} is not a saved dataset."
                )
            elif metric.get("column") not in columns[table]:
                errors.append(
                    f"{label}: column {metric.get('column')} is not "
                    f"selected in dataset {table}."
                )

        if not (metric.get("description") or "").strip():
            warnings.append(f"{label} has no description.")

    return errors, warnings
