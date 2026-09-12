from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from argus.config import read_config
from argus.modules.m5_critic import canonical
from argus.schema import Band, Claim, ClaimType, Evidence, Factor, Severity, Verification


def band_for(score: float) -> Band:
    return (
        Band.LOW if score < 25 else Band.MEDIUM if score < 50 else Band.HIGH if score < 75 else Band.CRITICAL
    )


def extract_factors(
    claims: list[Claim], verification: Verification, evidence: Evidence
) -> dict[str, tuple[float, list[str], bool]]:
    config = read_config("severity_factors.yaml")["factors"]
    result: dict[str, tuple[float, list[str], bool]] = {name: (0.0, [], False) for name in config}
    accepted = {
        v.claim_id: v
        for v in verification.claims
        if v.status == "VERIFIED" and v.final_type == ClaimType.OBSERVATION
    }
    for claim in claims:
        if claim.claim_id not in accepted:
            continue
        verification_claim = accepted[claim.claim_id]
        supporting = [
            d for d in evidence.objects if f"detection:{d.detection_id}" in verification_claim.evidence_refs
        ]
        entities = {canonical(d.cls) for d in supporting}
        count = max(
            (n for e, n in verification_claim.observed_counts.items() if canonical(e) == "person"), default=0
        )
        values = {
            "weapon_present": float(bool(entities & {"knife", "gun", "scissors"})),
            "people_involved": min(count / 10, 1),
            "crowd_density": min(count / 20, 1),
            "incident_duration": min((claim.time_span_s[1] - claim.time_span_s[0]) / 60, 1),
            "vehicle_involvement": float(bool(entities & {"car", "truck", "bus", "bicycle", "motorcycle"})),
            "detection_confidence": sum(d.conf for d in supporting) / len(supporting) if supporting else 0.0,
        }
        for name, raw in values.items():
            old, sources, _ = result[name]
            result[name] = (max(old, raw), sources + ([claim.claim_id] if raw > 0 else []), True)
    return result


def score(
    claims: list[Claim], verification: Verification, evidence: Evidence, model_path: Path | None = None
) -> Severity:
    values = extract_factors(claims, verification, evidence)
    config = read_config("severity_factors.yaml")["factors"]
    model: dict[str, Any] = json.loads(model_path.read_text()) if model_path and model_path.exists() else {}
    weights = model.get("weights", {name: row["weight"] for name, row in config.items()})
    if set(weights) != set(config) or any(float(w) < 0 for w in weights.values()):
        raise ValueError("Severity weights must contain exactly 13 nonnegative factors")
    factors = [
        Factor(
            name=name,
            raw=raw,
            weight=float(weights[name]),
            contribution=raw * float(weights[name]),
            source_claims=list(dict.fromkeys(sources)),
            available=available,
        )
        for name, (raw, sources, available) in values.items()
    ]
    value = min(100.0, sum(f.contribution for f in factors))
    return Severity(
        score=round(value, 2),
        band=band_for(value),
        factors=factors,
        model_version=model.get("version", "uncalibrated-reference-v1"),
        calibration_status=model.get(
            "calibration_status", "UNCALIBRATED reference weights; not a human-calibrated severity result"
        ),
    )
