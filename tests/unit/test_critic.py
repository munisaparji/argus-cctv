import pytest
from pydantic import ValidationError

from argus.modules.m5_critic import verify
from argus.modules.m6_severity import score
from argus.modules.m7_policy import validate_actions
from argus.schema import Claim, Detection, Evidence, VLMOutput


def evidence():
    return Evidence(
        objects=[
            Detection(
                detection_id=f"d{i}", cls=cls, conf=0.9, frame=25, time_s=1, bbox=(0, 0, 20, 40), track_id=i
            )
            for i, cls in enumerate(["person", "person", "bag"])
        ],
        tracks=[],
        counts={"person": 2, "bag": 1},
        keyframes=[],
        extractor="test",
    )


def claim(text="2 people are visible in the scene.", **kwargs):
    data = dict(
        claim_id="c1",
        text=text,
        type="OBSERVATION",
        entities=["person"],
        time_span_s=(0, 2),
        self_confidence=0.9,
        predicate="presence",
    )
    data.update(kwargs)
    return Claim(**data)


@pytest.mark.parametrize(
    "text,kwargs,reason",
    [
        ("A person is holding a knife.", {}, "no_supporting_detection"),
        ("3 people are visible.", {}, "count_mismatch"),
        ("2 people are visible.", {"time_span_s": (5, 8)}, "outside_window"),
        ("A knife is visible.", {"entities": []}, "no_supporting_detection"),
    ],
)
def test_rejected(text, kwargs, reason):
    result = verify([claim(text, **kwargs)], evidence(), (0, 3))
    assert result.n_rejected == 1
    assert result.claims[0].reason.startswith(reason)


@pytest.mark.parametrize(
    "text",
    [
        "The person intends to steal the bag.",
        "A person is running.",
        "The person is innocent.",
        "A person attacked another person.",
    ],
)
def test_uncheckable_prose_never_verified(text):
    result = verify([claim(text)], evidence(), (0, 3))
    assert result.claims[0].status == "DOWNGRADED"
    assert result.claims[0].final_type == "INFERENCE"


def test_empty_and_no_new_claims():
    assert verify([], evidence(), (0, 3)).hallucination_rate == 0
    c = claim()
    result = verify([c], evidence(), (0, 3))
    assert [r.claim_id for r in result.claims] == [c.claim_id]


def test_synonym_and_time_local_support():
    c = claim("A rucksack is visible.", entities=["rucksack"])
    result = verify([c], evidence(), (0, 3))
    assert result.n_verified == 1
    assert "rucksack->bag" in result.claims[0].alias_hits
    c.time_span_s = (2, 3)
    assert verify([c], evidence(), (0, 3)).n_rejected == 1


def test_rejected_does_not_change_severity():
    good = claim()
    bad = claim("A knife is visible.", claim_id="c2", entities=["knife"])
    e = evidence()
    baseline = score([good], verify([good], e, (0, 3)), e)
    combined = score([good, bad], verify([good, bad], e, (0, 3)), e)
    assert baseline == combined
    assert next(f for f in combined.factors if f.name == "weapon_present").raw == 0


@pytest.mark.parametrize(
    "payload",
    [
        {"claims": [], "severity": "HIGH"},
        {"claims": [], "actions": ["notify_police"]},
        {"claims": [], "extra": True},
    ],
)
def test_vlm_schema_forbids_downstream_fields(payload):
    with pytest.raises(ValidationError):
        VLMOutput.model_validate(payload)


def test_duplicate_claims_invalid():
    c = claim().model_dump()
    with pytest.raises(ValidationError):
        VLMOutput.model_validate({"claims": [c, c]})


def test_policy_strips_and_deduplicates():
    allowed, stripped = validate_actions(
        ["alert_guard", "kill", "alert_guard", "SEND_EMAIL", "preserve_clip"]
    )
    assert allowed == ["alert_guard", "preserve_clip"]
    assert stripped == ["kill", "SEND_EMAIL"]
