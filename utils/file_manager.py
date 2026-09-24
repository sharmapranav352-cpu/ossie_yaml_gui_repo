from pathlib import Path

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