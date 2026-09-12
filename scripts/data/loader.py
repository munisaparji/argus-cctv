import json
from pathlib import Path


def load_sirb(path: str):
    """Return a Hugging Face Dataset if the optional datasets package is installed."""
    from datasets import Dataset

    return Dataset.from_list(
        [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
    )
