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

    return list(
        OUTPUT_DIR.glob(
            "*.yaml"
        )
    )