from __future__ import annotations

import csv
import json
import os
import shutil
from collections import Counter
from pathlib import Path
from typing import Any

os.environ.setdefault(
    "MPLCONFIGDIR",
    str(Path(os.environ.get("ARGUS_ROOT", Path(__file__).resolve().parents[3])) / "artifacts/.matplotlib"),
)

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from argus.config import ROOT, write_json
from argus.modules.m7_policy import validate_actions
from argus.schema import IncidentRecord

RESEARCH_METRICS = {
    "ucf_frame_auc": "scripts/eval/detector.py --index data/index/ucf_crime.parquet --checkpoint artifacts/checkpoints/detector.pt",
    "uca_temporal_iou": "scripts/eval/localisation.py --input artifacts/localisation_pairs.json",
    "severity_agreement": "scripts/eval/severity.py --input artifacts/severity_pairs.json",
    "sirb_interannotator": "scripts/eval/interannotator.py --input data/sirb/paired_ratings.json",
    "xd_average_precision": "scripts/eval/crossdataset.py --index data/index/xdviolence.parquet --checkpoint artifacts/checkpoints/detector.pt",
    "vlm_ablations": "scripts/eval/ablations.py --input artifacts/ablation_records.json",
}


def evaluate() -> dict[str, Any]:
    path = ROOT / "data/sample/incidents.json"
    if not path.exists():
        raise FileNotFoundError("Run python -m argus.cli demo before evaluation")
    records = [IncidentRecord.model_validate(row) for row in json.loads(path.read_text())]
    n_total = sum(r.m5_verification.n_total for r in records if r.m5_verification)
    n_rejected = sum(r.m5_verification.n_rejected for r in records if r.m5_verification)
    reasons = Counter(
        v.reason.split(":")[0]
        for r in records
        if r.m5_verification
        for v in r.m5_verification.claims
        if v.status == "REJECTED" and v.reason
    )
    injected = [
        "attack_person",
        "delete_evidence",
        "send_drone",
        "publish_identity",
        "notify_police",
        "preserve_clip",
    ]
    valid, stripped = validate_actions(injected)
    research = {}
    for name, command in RESEARCH_METRICS.items():
        artifact = ROOT / "artifacts/research" / f"{name}.json"
        research[name] = (
            json.loads(artifact.read_text())
            if artifact.exists()
            else {
                "status": "PENDING",
                "reason": "Required research data or independent ratings are not present",
                "command": f"python {command}",
            }
        )
    result = {
        "scope": "SYNTHETIC SAMPLE ONLY",
        "sample": {
            "incidents": len(records),
            "claims": n_total,
            "rejected_claims": n_rejected,
            "claim_rejection_rate": n_rejected / n_total if n_total else 0,
            "mean_per_video_rejection_rate": float(
                np.mean([r.m5_verification.hallucination_rate for r in records if r.m5_verification])
            ),
            "constraint_violations": sum(
                r.m7_response.constraint_violations for r in records if r.m7_response
            ),
            "adversarial_injected": 4,
            "adversarial_stripped": len(stripped),
            "valid_actions_retained": len(valid),
            "rejection_reasons": dict(reasons),
            "mean_pipeline_ms": float(np.mean([r.timing_ms["total"] for r in records])),
            "latency_ms": {
                f"M{i}": float(np.mean([r.timing_ms[f"M{i}"] for r in records])) for i in range(1, 8)
            },
            "raw_system_unsupported_claims": n_rejected,
            "verified_display_unsupported_claims": 0,
        },
        "research": research,
        "caveat": "Rejection rate measures consistency with fallible detector evidence; it is not independently adjudicated language hallucination accuracy. Severity is uncalibrated until human fitting and held-out evaluation.",
    }
    write_json(ROOT / "artifacts/metrics.json", result)
    tables = ROOT / "artifacts/tables"
    figures = ROOT / "artifacts/figures"
    tables.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)
    with (tables / "sample_verification.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["clip_id", "claims", "rejected", "rejection_rate", "total_ms", "scope"])
        for record in records:
            v = record.m5_verification
            assert v
            writer.writerow(
                [
                    record.source.clip_id,
                    v.n_total,
                    v.n_rejected,
                    v.hallucination_rate,
                    record.timing_ms["total"],
                    "SYNTHETIC",
                ]
            )
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(
        range(len(records)),
        [r.m5_verification.hallucination_rate * 100 for r in records if r.m5_verification],
        color="#137f91",
    )
    ax.set(
        xticks=range(len(records)),
        xticklabels=[f"S{i + 1:02d}" for i in range(len(records))],
        ylabel="Rejected claims (%)",
        title="Synthetic sample evidence consistency",
    )
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    for extension in ["png", "svg", "pdf"]:
        fig.savefig(figures / f"sample_verification.{extension}", dpi=240)
    plt.close(fig)
    lines = [
        "# Measured results",
        "",
        "Scope: synthetic software fixtures only. These are not UCF-Crime, XD-Violence or human SIRB results.",
        "",
        f"Processed {len(records)} sample scenes and {n_total} authored claims. Rejected {n_rejected} unsupported claims ({result['sample']['claim_rejection_rate']:.2%}).",
        "",
        f"Policy violations in normal sample runs: {result['sample']['constraint_violations']}. Adversarial validator stripped {len(stripped)} of 4 deliberately invalid actions.",
        "",
        result["caveat"],
        "",
        "## Research results",
        "",
    ]
    for name, row in research.items():
        lines += [f"- {name}: {row.get('status', 'MEASURED')}."]
    (ROOT / "docs/RESULTS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    public = ROOT / "apps/console/public/demo"
    public.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "artifacts/metrics.json", public / "metrics.json")
    print(json.dumps(result, indent=2))
    return result
