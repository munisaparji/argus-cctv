from __future__ import annotations

import json
import logging
import subprocess
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from argus.config import ROOT, digest, read_config, seed_all, write_json
from argus.modules import (
    m1_preprocess,
    m2_detection,
    m3_evidence,
    m4_reasoning,
    m5_critic,
    m6_severity,
    m7_policy,
)
from argus.schema import IncidentRecord, Provenance, Source

MODULE_NAMES = ["Preprocess", "Localise", "Evidence", "Reason", "Verify", "Severity", "Policy"]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run(
    source: Source,
    cache_path: Path,
    checkpoint: Path | None = None,
    severity_model: Path | None = None,
    device: str = "cpu",
    on_event: Callable[[dict[str, Any]], None] | None = None,
    retry_cache: Path | None = None,
    blur_faces: bool = False,
) -> IncidentRecord:
    config = read_config("config.yaml")
    seed_all(int(config["seed"]))
    try:
        sha = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, stderr=subprocess.DEVNULL, text=True
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        sha = "uncommitted"
    record = IncidentRecord(
        incident_id=f"{source.clip_id}_{uuid.uuid4().hex[:8]}",
        source=source,
        pipeline=Provenance(
            run_id=uuid.uuid4().hex,
            started_at=utc_now(),
            config_hash=digest(config),
            git_sha=sha,
            seed=config["seed"],
            module_versions={f"M{i}": "1.0.0" for i in range(1, 8)},
        ),
    )
    total = time.perf_counter()
    for number, label in enumerate(MODULE_NAMES, 1):
        module = f"M{number}"
        started = time.perf_counter()
        if on_event:
            on_event({"module": module, "label": label, "status": "running"})
        if number == 1:
            record.m1_features = m1_preprocess.extract(ROOT / source.video_path, source.sample, device)
        elif number == 2:
            assert record.m1_features
            record.m2_detection = m2_detection.detect(
                record.m1_features, ROOT, source.duration_s, source.sample, checkpoint, device
            )
        elif number == 3:
            assert record.m2_detection
            detector = m3_evidence.SyntheticDetector() if source.sample else m3_evidence.DetrDetector(device)
            record.m3_evidence = m3_evidence.build_evidence(
                ROOT / source.video_path,
                record.m2_detection.t_start_s,
                record.m2_detection.t_end_s,
                ROOT / "data/cache/evidence" / record.incident_id,
                ROOT,
                detector,
                blur_faces,
            )
        elif number == 4:
            output = m4_reasoning.load_claims(cache_path)
            record.m4_claims = output.claims
            record.m4_attempts = [output]
        elif number == 5:
            assert record.m3_evidence and record.m2_detection
            window = (record.m2_detection.t_start_s, record.m2_detection.t_end_s)
            verification = m5_critic.verify(record.m4_claims, record.m3_evidence, window)
            if (
                verification.hallucination_rate > config["retry_threshold"]
                and retry_cache
                and retry_cache.exists()
            ):
                retry = m4_reasoning.load_claims(retry_cache)
                record.m4_attempts.append(retry)
                original_rate = verification.hallucination_rate
                record.m4_claims = retry.claims
                verification = m5_critic.verify(retry.claims, record.m3_evidence, window)
                verification.retry_used = True
                verification.original_rejection_rate = original_rate
            record.m5_verification = verification
        elif number == 6:
            assert record.m5_verification and record.m3_evidence
            record.m6_severity = m6_severity.score(
                record.m4_claims, record.m5_verification, record.m3_evidence, severity_model
            )
        elif number == 7:
            assert record.m2_detection and record.m6_severity
            record.m7_response = m7_policy.recommend(
                record.m2_detection.incident_class, record.m6_severity.band
            )
        record.timing_ms[module] = round((time.perf_counter() - started) * 1000, 3)
        logging.getLogger("argus").info(
            json.dumps(
                {
                    "run_id": record.pipeline.run_id,
                    "incident_id": record.incident_id,
                    "module": module,
                    "latency_ms": record.timing_ms[module],
                }
            )
        )
        if on_event:
            on_event(
                {
                    "module": module,
                    "label": label,
                    "status": "complete",
                    "latency_ms": record.timing_ms[module],
                    "record": record.model_dump(mode="json"),
                }
            )
    record.pipeline.finished_at = utc_now()
    record.timing_ms["total"] = round((time.perf_counter() - total) * 1000, 3)
    assert record.human.state == "AWAITING_HUMAN_CONFIRMATION"
    write_json(ROOT / "artifacts/runs" / f"{record.incident_id}.json", record.model_dump(mode="json"))
    return record
