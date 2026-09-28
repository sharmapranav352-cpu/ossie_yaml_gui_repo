"""
Writes the semantic model as an Apache Ossie YAML document in the standard
layout used by project-compass-SIT/ossie-semantic-contracts:

    version: 0.2.0.dev0
    name: ...
    description: ...
    datasets: [...]
    relationships: [...]
    metrics: [...]

The model properties sit at the document root (no `semantic_model:` wrapper),
list items are indented under their key, and strings containing double quotes
are written in double-quoted style, so the output matches that repo's files
line for line.
"""

import yaml

OSSIE_VERSION = "0.2.0.dev0"


class _OssieDumper(yaml.SafeDumper):
    """Two-space indent with list items indented under their key, no anchors."""

    def ignore_aliases(self, data):
        return True

    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)


def _str_representer(dumper, value):
    # JSON-like strings such as {"access_modifier":"public_access"} are
    # written as "{\"access_modifier\":\"public_access\"}"
    style = '"' if '"' in value else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", value, style=style)


_OssieDumper.add_representer(str, _str_representer)


class OssieGenerator:

    @staticmethod
    def generate(
        model_name,
        description,
        datasets,
        relationships,
        metrics
    ):

        payload = {
            "version": OSSIE_VERSION,
            "name": model_name,
        }

        if description:
            payload["description"] = description

        payload["datasets"] = datasets

        if relationships:
            payload["relationships"] = relationships

        if metrics:
            payload["metrics"] = metrics

        return yaml.dump(
            payload,
            Dumper=_OssieDumper,
            sort_keys=False,
            default_flow_style=False,
            allow_unicode=True,
            width=4096,
        )
