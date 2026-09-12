from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from argus.schema import VLMOutput


def load_claims(path: Path) -> VLMOutput:
    if not path.is_file():
        raise FileNotFoundError(f"No VLM cache: {path}. Run scripts/batch_vlm.py with the research extras.")
    return VLMOutput.model_validate_json(path.read_text(encoding="utf-8"))


def generate_validated(generate: Callable[[str], str], prompt: str, attempts: int = 3) -> VLMOutput:
    if not 1 <= attempts <= 3:
        raise ValueError("At most three JSON generation attempts are permitted")
    errors = []
    for _ in range(attempts):
        try:
            # WHY: Strict JSON parsing must reject prose and extra keys, including action and severity.
            return VLMOutput.model_validate(json.loads(generate(prompt)))
        except (ValueError, TypeError) as error:
            errors.append(str(error))
    raise ValueError(f"VLM failed schema validation after {attempts} attempts: {errors[-1]}")
