from pathlib import Path

# Every generated model is saved under this one name, locally and on GitHub.
# Set to None to name files after the model instead.
FIXED_OUTPUT_FILE = "SALES_AND_ORDERS.yaml"

# The model name the file must carry. SALES_AND_ORDERS.yaml is synced to
# ossie-semantic-contracts, which deploys it as this semantic view.
# Set to None to allow any name.
EXPECTED_MODEL_NAME = "SALES_AND_ORDERS"

OUTPUT_DIR = Path(
    "outputs"
)

OUTPUT_DIR.mkdir(
    exist_ok=True
)

def save_yaml(
    filename,
    content
):

    file_path = (
        OUTPUT_DIR / filename
    )

    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(content)

    return file_path


def list_yamls():

    return sorted(
        list(OUTPUT_DIR.glob("*.yaml")) + list(OUTPUT_DIR.glob("*.yml")),
        key=lambda p: p.name.lower()
    )


def read_yaml(filename):

    path = OUTPUT_DIR / Path(filename).name

    return path.read_text(encoding="utf-8") if path.exists() else None