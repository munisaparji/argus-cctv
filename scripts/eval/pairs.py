import argparse
import json
from pathlib import Path

from argus.config import ROOT, write_json
from argus.eval.metrics import agreement
from argus.modules.m2_detection import temporal_iou


def main(kind: str) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    rows = json.loads(args.input.read_text())
    if not rows:
        raise ValueError("No evaluation rows")
    if kind == "uca_temporal_iou":
        values = [temporal_iou(tuple(r["predicted"]), tuple(r["truth"])) for r in rows]
        result = {"mean_tiou": sum(values) / len(values), "values": values, "n": len(values)}
    else:
        if kind == "severity_agreement" and any(r.get("split") != "test" for r in rows):
            raise ValueError("Severity evaluation requires held-out test ratings")
        result = agreement([r["a"] for r in rows], [r["b"] for r in rows])
    result["status"] = "MEASURED"
    write_json(ROOT / "artifacts/research" / f"{kind}.json", result)
    print(json.dumps(result, indent=2))
