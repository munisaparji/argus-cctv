"""Authored Robbery051 contract example; never evidence of a real clip experiment."""

from argus.modules.m5_critic import verify
from argus.modules.m7_policy import recommend
from argus.schema import Band, Claim, Detection, Evidence


def test_rejected_knife_trace():
    evidence = Evidence(
        objects=[
            Detection(
                detection_id=f"d{i}",
                cls=c,
                conf=0.95,
                frame=1100,
                time_s=44,
                bbox=(i * 30, 20, 25, 50),
                track_id=i,
            )
            for i, c in enumerate(["person", "person", "bag"])
        ],
        tracks=[],
        counts={"person": 2, "bag": 1},
        keyframes=[],
        extractor="authored golden fixture",
    )
    claims = [
        Claim(
            claim_id="c1",
            text="2 people are visible.",
            type="OBSERVATION",
            entities=["person"],
            time_span_s=(43, 46),
            self_confidence=0.9,
            predicate="count",
            counts={"person": 2},
        ),
        Claim(
            claim_id="c2",
            text="A knife is visible.",
            type="OBSERVATION",
            entities=["knife"],
            time_span_s=(43, 46),
            self_confidence=0.95,
            predicate="presence",
        ),
    ]
    result = verify(claims, evidence, (43, 51))
    assert result.claims[0].status == "VERIFIED"
    assert result.claims[1].reason == "no_supporting_detection:knife"
    assert recommend("Robbery", Band.HIGH).recommended_actions == [
        "alert_guard",
        "preserve_clip",
        "notify_police",
    ]
    # WHY: The brief's illustrative score 72 cannot be a measured golden target before fitting on humans.
