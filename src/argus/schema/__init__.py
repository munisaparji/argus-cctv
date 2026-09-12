from __future__ import annotations

from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Probability = Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)]
Span = tuple[Annotated[float, Field(ge=0)], Annotated[float, Field(ge=0)]]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True, allow_inf_nan=False)


class ClaimType(str, Enum):
    OBSERVATION = "OBSERVATION"
    INFERENCE = "INFERENCE"
    UNCERTAINTY = "UNCERTAINTY"


class Band(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Action(str, Enum):
    log_only = "log_only"
    alert_guard = "alert_guard"
    preserve_clip = "preserve_clip"
    notify_supervisor = "notify_supervisor"
    notify_police = "notify_police"
    call_medical = "call_medical"
    call_fire = "call_fire"
    lock_down_zone = "lock_down_zone"
    dispatch_patrol = "dispatch_patrol"
    request_second_camera = "request_second_camera"
    flag_for_review = "flag_for_review"
    escalate_human = "escalate_human"


class Claim(StrictModel):
    claim_id: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,80}$")
    text: str = Field(min_length=1, max_length=1000)
    type: ClaimType
    entities: list[str] = Field(max_length=30)
    time_span_s: Span
    self_confidence: Probability
    predicate: Literal["presence", "count", "motion", "contact", "damage", "intent", "unknown"] = "unknown"
    counts: dict[str, Annotated[int, Field(ge=0)]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def valid_span(self) -> Claim:
        if self.time_span_s[1] < self.time_span_s[0]:
            raise ValueError("Time span must be ordered")
        return self


class VLMOutput(StrictModel):
    claims: list[Claim] = Field(max_length=50)

    @model_validator(mode="after")
    def unique_ids(self) -> VLMOutput:
        if len({c.claim_id for c in self.claims}) != len(self.claims):
            raise ValueError("Claim IDs must be unique")
        return self


class Detection(StrictModel):
    detection_id: str
    cls: str
    conf: Probability
    frame: int = Field(ge=0)
    time_s: float = Field(ge=0)
    bbox: tuple[float, float, float, float]
    track_id: int = Field(ge=0)


class Track(StrictModel):
    track_id: int
    cls: str
    frames: list[int]
    trajectory: list[tuple[float, float]]


class Keyframe(StrictModel):
    frame: int
    time_s: float
    path: str
    reason: str


class Evidence(StrictModel):
    objects: list[Detection]
    tracks: list[Track]
    counts: dict[str, int]
    keyframes: list[Keyframe]
    extractor: str
    # WHY: A detector is fallible; support is evidence consistency, never proof of truth.
    limitations: list[str] = Field(default_factory=list)


class VerificationClaim(StrictModel):
    claim_id: str
    status: Literal["VERIFIED", "REJECTED", "DOWNGRADED", "UNCERTAINTY"]
    evidence_refs: list[str]
    reason: str | None = None
    original_type: ClaimType
    final_type: ClaimType
    alias_hits: list[str] = Field(default_factory=list)
    observed_counts: dict[str, int] = Field(default_factory=dict)


class Verification(StrictModel):
    claims: list[VerificationClaim]
    hallucination_rate: Probability
    n_total: int
    n_verified: int
    n_rejected: int
    n_downgraded: int
    retry_used: bool = False
    original_rejection_rate: Probability = 0


class Factor(StrictModel):
    name: str
    raw: Probability
    weight: float = Field(ge=0)
    contribution: float = Field(ge=0)
    source_claims: list[str]
    available: bool = True


class Severity(StrictModel):
    score: float = Field(ge=0, le=100)
    band: Band
    factors: list[Factor]
    model_version: str
    calibration_status: str


class Response(StrictModel):
    recommended_actions: list[Action]
    policy_rule_id: str
    constraint_violations: int = Field(ge=0)
    stripped_actions: list[str]


class Source(StrictModel):
    dataset: str
    clip_id: str
    video_path: str
    fps: float = Field(gt=0)
    duration_s: float = Field(gt=0)
    sample: bool
    split: Literal["train", "val", "test", "demo"] = "demo"


class Features(StrictModel):
    cache_path: str
    n_snippets: int = Field(gt=0)
    feature_dim: int = Field(gt=0)
    extractor: str
    cache_key: str
    snippet_s: float = Field(gt=0)


class Localisation(StrictModel):
    score_curve: list[Probability]
    t_start_s: float = Field(ge=0)
    t_end_s: float = Field(ge=0)
    incident_class: str
    class_confidence: Probability
    model_version: str
    gt_window_s: Span | None = None
    temporal_iou: Probability | None = None


class Provenance(StrictModel):
    run_id: str
    started_at: str
    finished_at: str | None = None
    config_hash: str
    git_sha: str
    seed: int
    module_versions: dict[str, str]


class Human(StrictModel):
    state: Literal["AWAITING_HUMAN_CONFIRMATION", "CONFIRMED", "DISMISSED"] = "AWAITING_HUMAN_CONFIRMATION"
    decision: Literal["confirm", "dismiss"] | None = None
    operator_note: str | None = None
    decided_at: str | None = None


class IncidentRecord(StrictModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    incident_id: str
    source: Source
    pipeline: Provenance
    m1_features: Features | None = None
    m2_detection: Localisation | None = None
    m3_evidence: Evidence | None = None
    m4_claims: list[Claim] = Field(default_factory=list)
    m4_attempts: list[VLMOutput] = Field(default_factory=list)
    m5_verification: Verification | None = None
    m6_severity: Severity | None = None
    m7_response: Response | None = None
    human: Human = Field(default_factory=Human)
    timing_ms: dict[str, float] = Field(default_factory=dict)


class DecisionRequest(StrictModel):
    decision: Literal["confirm", "dismiss"]
    operator: str = Field(min_length=1, max_length=80)
    note: str = Field(default="", max_length=2000)

    @model_validator(mode="after")
    def dismiss_note(self) -> DecisionRequest:
        if not self.operator.strip() or (self.decision == "dismiss" and not self.note.strip()):
            raise ValueError("Operator is required; dismiss requires an operator note")
        return self


class EvidenceSpan(StrictModel):
    start_s: float = Field(ge=0)
    end_s: float = Field(ge=0)
    label: str = Field(min_length=1, max_length=200)

    @model_validator(mode="after")
    def ordered(self) -> EvidenceSpan:
        if self.end_s < self.start_s:
            raise ValueError("End must follow start")
        return self


class Annotation(StrictModel):
    clip_id: str
    annotator: str = Field(min_length=1, max_length=80)
    score: float = Field(ge=0, le=100)
    factors: dict[str, Probability]
    actions: list[Action]
    spans: list[EvidenceSpan]
    note: str = Field(default="", max_length=2000)
    complete: bool = False
    accepted_suggestions: list[str] = Field(default_factory=list)
    adjudication: bool = False
