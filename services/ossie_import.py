"""
Read an existing OSSIE YAML file back into the app's saved configuration,
so it can be edited on the Datasets, Relationships and Metrics pages and
written out again.

parse_ossie_yaml(text) -> (config, notes)
  config  same shape as st.session_state.saved
  notes   plain-language list of anything that could not be carried over
"""

import re

import yaml

# SUM(TABLE.COLUMN), COUNT(DISTINCT TABLE.COLUMN), ...
_AGG = re.compile(
    r"^\s*(SUM|AVG|COUNT|MIN|MAX)\s*\(\s*(DISTINCT\s+)?"
    r"([A-Za-z_][\w$]*)\.([A-Za-z_][\w$]*)\s*\)\s*$",
    re.IGNORECASE,
)

KNOWN_MODEL_KEYS = {"name", "description", "datasets", "relationships", "metrics"}
KNOWN_DATASET_KEYS = {"name", "source", "fields", "primary_key"}
KNOWN_FIELD_KEYS = {"name", "expression", "custom_extensions", "dimension"}
KNOWN_REL_KEYS = {"name", "from", "to", "from_columns", "to_columns"}
KNOWN_METRIC_KEYS = {"name", "expression", "description", "custom_extensions"}


class OssieImportError(ValueError):
    pass


def _snowflake_expression(obj):
    """Pull the SNOWFLAKE dialect expression out of an OSSIE expression block."""
    if isinstance(obj, str):
        return obj
    dialects = (obj or {}).get("dialects") or []
    for d in dialects:
        if str(d.get("dialect", "")).upper() == "SNOWFLAKE":
            return str(d.get("expression", ""))
    return str(dialects[0].get("expression", "")) if dialects else ""


def _extra_keys(obj, known, label, notes):
    extra = sorted(set(obj) - known)
    if extra:
        notes.append(f"{label}: {', '.join(extra)} not supported by the editor and will be dropped on save.")


def parse_ossie_yaml(text):
    try:
        doc = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise OssieImportError(f"This isn't valid YAML: {exc}") from exc

    if not isinstance(doc, dict) or not doc.get("semantic_model"):
        raise OssieImportError(
            "This doesn't look like an OSSIE file: no semantic_model section."
        )

    models = doc["semantic_model"]
    if isinstance(models, dict):
        models = [models]

    notes = []
    if len(models) > 1:
        notes.append(
            f"The file has {len(models)} semantic models. Only the first, "
            f"{models[0].get('name')}, was opened."
        )

    model = models[0]
    _extra_keys(model, KNOWN_MODEL_KEYS, "Model", notes)

    # ---- datasets ----------------------------------------------------------
    tables = []
    scopes = []

    for ds in model.get("datasets") or []:
        name = ds.get("name")
        source = ds.get("source") or ""
        parts = source.split(".")

        if len(parts) == 3:
            scopes.append((parts[0], parts[1]))
        else:
            notes.append(f"Dataset {name}: source '{source}' isn't DATABASE.SCHEMA.TABLE.")

        _extra_keys(ds, KNOWN_DATASET_KEYS, f"Dataset {name}", notes)

        columns, time_columns = [], []
        for field in ds.get("fields") or []:
            fname = field.get("name")
            expr = _snowflake_expression(field.get("expression"))
            if expr and expr != fname:
                notes.append(
                    f"Dataset {name}: field {fname} uses the expression '{expr}'. "
                    "The editor stores fields as plain columns, so it will be saved as "
                    f"column {fname}."
                )
            _extra_keys(field, KNOWN_FIELD_KEYS, f"Field {name}.{fname}", notes)

            columns.append(fname)
            if (field.get("dimension") or {}).get("is_time"):
                time_columns.append(fname)

        pk = ds.get("primary_key") or []
        if isinstance(pk, str):
            pk = [pk]

        tables.append({
            "name": name,
            "source": source,
            "selected_columns": columns,
            "primary_keys": [c for c in pk if c in columns],
            "time_columns": time_columns,
            "column_types": {},
        })

    database, schema = (scopes[0] if scopes else (None, None))
    if len(set(scopes)) > 1:
        notes.append(
            "Datasets come from more than one schema. The Datasets page edits "
            f"one schema at a time, so it opens {database}.{schema}; saving "
            "datasets there replaces the others."
        )

    # ---- relationships -----------------------------------------------------
    relationships = []
    for rel in model.get("relationships") or []:
        from_cols = rel.get("from_columns") or []
        to_cols = rel.get("to_columns") or []
        from_t, to_t = rel.get("from"), rel.get("to")
        _extra_keys(rel, KNOWN_REL_KEYS, f"Relationship {rel.get('name')}", notes)

        if len(from_cols) > 1 or len(to_cols) > 1:
            notes.append(
                f"Relationship {rel.get('name')} joins on several columns; "
                "the editor keeps the first pair only."
            )

        name = rel.get("name") or ""
        relationships.append({
            # Blank means "use the automatic name", so keep it blank if it matches
            "name": "" if name == f"{from_t}_TO_{to_t}" else name,
            "from_table": from_t,
            "from_column": from_cols[0] if from_cols else None,
            "to_table": to_t,
            "to_column": to_cols[0] if to_cols else None,
        })

    # ---- metrics -----------------------------------------------------------
    metrics = []
    for m in model.get("metrics") or []:
        _extra_keys(m, KNOWN_METRIC_KEYS, f"Metric {m.get('name')}", notes)
        expr = _snowflake_expression(m.get("expression"))
        match = _AGG.match(expr)

        metric = {
            "name": m.get("name") or "",
            "description": m.get("description") or "",
            "type": "CUSTOM",
            "table": None,
            "column": None,
            "expression": expr,
        }

        if match:
            func, distinct, table, column = match.groups()
            func = func.upper()
            metric.update({
                "type": "COUNT DISTINCT" if distinct and func == "COUNT" else func,
                "table": table,
                "column": column,
                "expression": "",
            })
            if distinct and func != "COUNT":
                metric.update({"type": "CUSTOM", "table": None,
                               "column": None, "expression": expr})

        metrics.append(metric)

    config = {
        "model": {
            "name": model.get("name") or "MY_MODEL",
            "description": model.get("description") or "",
        },
        "datasets": {"database": database, "schema": schema, "tables": tables},
        "relationships": relationships,
        "metrics": metrics,
    }

    return config, notes
