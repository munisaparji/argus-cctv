import argparse
import json
from pathlib import Path

from argus.config import ROOT, write_json

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    rows = json.loads(args.input.read_text())
    variants = {}
    for row in rows:
        variants.setdefault(row["variant"], []).append(row)
    required = {"7b_evidence_critic", "7b_no_evidence_critic", "3b_evidence_critic", "7b_evidence_no_critic"}
    if not required <= set(variants):
        raise ValueError(f"Required ablations: {sorted(required)}")
    reference = {r["clip_id"] for r in variants["7b_evidence_critic"]}
    result = {"status": "MEASURED", "variants": {}}
    for name, values in variants.items():
        if {r["clip_id"] for r in values} != reference or len(values) != len(reference):
            raise ValueError("All ablations must use the same clips exactly once")
        count = sum(r["n_claims"] for r in values)
        result["variants"][name] = {
            "n_clips": len(values),
            "claim_rejection_rate": sum(r["n_rejected"] for r in values) / count if count else 0,
        }
    write_json(ROOT / "artifacts/research/vlm_ablations.json", result)
    print(json.dumps(result, indent=2))
