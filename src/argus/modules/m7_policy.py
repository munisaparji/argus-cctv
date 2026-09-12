from __future__ import annotations

from argus.config import read_config
from argus.schema import Action, Band, Response


def validate_actions(actions: list[str]) -> tuple[list[Action], list[str]]:
    vocabulary = {a.value for a in Action}
    valid = list(dict.fromkeys(Action(a) for a in actions if a in vocabulary))
    stripped = [a for a in actions if a not in vocabulary]
    return valid, stripped


def recommend(category: str, band: Band) -> Response:
    policy = read_config("policy_table.yaml")
    key = category if category in policy else "default"
    valid, stripped = validate_actions(policy[key][band.value])
    return Response(
        recommended_actions=valid,
        policy_rule_id=f"{key.lower()}.{band.value.lower()}",
        constraint_violations=len(stripped),
        stripped_actions=stripped,
    )
