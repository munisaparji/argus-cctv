from __future__ import annotations

import re
from collections import Counter
from typing import Literal

from argus.schema import Claim, ClaimType, Evidence, Verification, VerificationClaim

ALIASES = {
    "people": "person",
    "persons": "person",
    "man": "person",
    "men": "person",
    "woman": "person",
    "women": "person",
    "rucksack": "bag",
    "backpack": "bag",
    "handbag": "bag",
    "automobile": "car",
    "vehicles": "vehicle",
    "knives": "knife",
    "firearm": "gun",
    "pistol": "gun",
}
HYPERNYMS = {
    "weapon": {"knife", "gun", "scissors"},
    "vehicle": {"car", "truck", "bus", "motorcycle", "bicycle"},
}
KNOWN = {
    "person",
    "bag",
    "knife",
    "gun",
    "weapon",
    "car",
    "truck",
    "bus",
    "bicycle",
    "motorcycle",
    "vehicle",
    "scissors",
    "counter",
    "fire",
    "smoke",
} | set(ALIASES)
NUMBERS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
}
INTENT = re.compile(r"\b(intend\w*|motive|planning|plans|wants|trying|steal\w*|threaten\w*|rob\w*)\b", re.I)
EVENT = re.compile(
    r"\b(hold\w*|handing|attack\w*|hit\w*|punch\w*|fight\w*|damag\w*|break\w*|running|walking|approach\w*|contact|carrying|stand\w*)\b",
    re.I,
)
SAFE_PRESENCE = re.compile(
    r"(?:a|an|one|two|three|four|five|six|seven|eight|nine|ten|\d+) (?:person|people|persons|bag|bags|backpack|backpacks|rucksack|car|cars|truck|bus|vehicle|knife|gun|weapon|scissors) (?:is|are) visible(?: in the scene)?[.!]?",
    re.I,
)


def canonical(name: str) -> str:
    name = name.lower().strip()
    if name in ALIASES:
        return ALIASES[name]
    return name[:-1] if name.endswith("s") and name[:-1] in KNOWN else name


def matches(claimed: str, observed: str) -> bool:
    target, actual = canonical(claimed), canonical(observed)
    return target == actual or actual in HYPERNYMS.get(target, set())


def verify(claims: list[Claim], evidence: Evidence, window: tuple[float, float]) -> Verification:
    results = []
    for claim in claims:
        status: Literal["VERIFIED", "REJECTED", "DOWNGRADED", "UNCERTAINTY"] = "VERIFIED"
        reason = None
        final_type = claim.type
        aliases: list[str] = []
        refs: set[str] = set()
        start, end = claim.time_span_s
        observed_counts: dict[str, int] = {}
        entities = set(claim.entities)
        # WHY: Inspect prose too; an untrusted generator may omit an unsupported entity from metadata.
        tokens = re.findall(r"\b[a-z]+\b", claim.text.lower())
        entities.update(token for token in tokens if token in KNOWN or canonical(token) in KNOWN)
        declared_counts = dict(claim.counts)
        for number, noun in re.findall(
            r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+(\w+)", claim.text.lower()
        ):
            if noun in KNOWN or canonical(noun) in KNOWN:
                declared_counts[noun] = int(number) if number.isdigit() else NUMBERS[number]
        available = [
            d for d in evidence.objects if start <= d.time_s <= end and window[0] <= d.time_s <= window[1]
        ]
        if start < window[0] or end > window[1]:
            status, reason = "REJECTED", "outside_window"
        elif not entities and claim.type == ClaimType.OBSERVATION:
            status, reason = "DOWNGRADED", "no_checkable_entities"
        else:
            for entity in sorted(entities | set(declared_counts)):
                canonical_entity = canonical(entity)
                if canonical_entity != entity:
                    aliases.append(f"{entity}->{canonical_entity}")
                supporting = [d for d in available if matches(entity, d.cls)]
                frame_counts = Counter(d.frame for d in supporting)
                observed_counts[entity] = max(frame_counts.values(), default=0)
                if not supporting:
                    status, reason = "REJECTED", f"no_supporting_detection:{entity}"
                    break
                refs.update(f"detection:{d.detection_id}" for d in supporting)
                refs.update(f"track:{d.track_id}" for d in supporting)
                if entity in declared_counts and declared_counts[entity] != observed_counts[entity]:
                    status, reason = (
                        "REJECTED",
                        f"count_mismatch:{entity}:claimed={declared_counts[entity]}:observed={observed_counts[entity]}",
                    )
                    break
        if status != "REJECTED":
            if claim.type == ClaimType.UNCERTAINTY:
                status = "UNCERTAINTY"
            elif (
                claim.type == ClaimType.INFERENCE
                or claim.predicate in {"intent", "motion", "contact", "damage", "unknown"}
                or INTENT.search(claim.text)
                or EVENT.search(claim.text)
                or not SAFE_PRESENCE.fullmatch(claim.text.strip())
            ):
                status, reason, final_type = "DOWNGRADED", "unverifiable_from_pixels", ClaimType.INFERENCE
            elif status == "DOWNGRADED":
                final_type = ClaimType.INFERENCE
        results.append(
            VerificationClaim(
                claim_id=claim.claim_id,
                status=status,
                evidence_refs=sorted(refs),
                reason=reason,
                original_type=claim.type,
                final_type=final_type,
                alias_hits=aliases,
                observed_counts=observed_counts,
            )
        )
    assert [c.claim_id for c in results] == [c.claim_id for c in claims], (
        "Critic cannot add or replace claims"
    )
    rejected = sum(r.status == "REJECTED" for r in results)
    rate = rejected / len(results) if results else 0.0
    return Verification(
        claims=results,
        hallucination_rate=rate,
        n_total=len(results),
        n_verified=sum(r.status == "VERIFIED" for r in results),
        n_rejected=rejected,
        n_downgraded=sum(r.status == "DOWNGRADED" for r in results),
        original_rejection_rate=rate,
    )
