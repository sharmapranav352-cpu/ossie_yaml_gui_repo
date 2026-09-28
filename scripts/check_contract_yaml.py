"""
Checks outputs/SIT_YAML_GUI.yaml before it is copied to
project-compass-SIT/ossie-semantic-contracts, where merging it deploys a
semantic view to Snowflake.

Usage: python check_contract_yaml.py <file> <expected model name>
Exits non-zero with a plain explanation if the file must not be synced.
"""
import sys

import yaml

REQUIRED_VERSION = "0.2.0.dev0"


def main():
    path, expected_name = sys.argv[1], sys.argv[2]
    try:
        doc = yaml.safe_load(open(path, encoding="utf-8"))
    except yaml.YAMLError as exc:
        sys.exit(f"{path} is not valid YAML: {exc}")

    problems = []
    if not isinstance(doc, dict):
        sys.exit(f"{path} must be a YAML mapping.")
    if str(doc.get("version")) != REQUIRED_VERSION:
        problems.append(f"version is '{doc.get('version')}', expected '{REQUIRED_VERSION}'")
    if "semantic_model" in doc:
        problems.append("uses the old 'semantic_model:' wrapper; the model must be at the top level")
    if doc.get("name") != expected_name:
        problems.append(
            f"model name is '{doc.get('name')}', expected '{expected_name}'. "
            "Syncing another name would deploy a different semantic view."
        )
    if not doc.get("datasets"):
        problems.append("has no datasets")

    if problems:
        print(f"Not syncing {path}:")
        for p in problems:
            print(f"  - {p}")
        sys.exit(1)

    print(f"{path} is OK: {expected_name}, version {REQUIRED_VERSION}, "
          f"{len(doc['datasets'])} datasets, "
          f"{len(doc.get('relationships') or [])} relationships, "
          f"{len(doc.get('metrics') or [])} metrics.")


if __name__ == "__main__":
    main()
