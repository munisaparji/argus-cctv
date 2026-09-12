import argparse
import json
from pathlib import Path

from argus.train.severity import fit

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("artifacts/checkpoints/severity.json"))
    args = parser.parse_args()
    print(json.dumps(fit(json.loads(args.input.read_text()), args.output), indent=2))
