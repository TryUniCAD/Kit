from typing import cast


# api responses must remain data rather than executable workflow instructions
def ObjectMap(Value: object) -> dict[str, object]:
    if not isinstance(Value, dict):
        raise ValueError("Expected a JSON object")
    return cast(dict[str, object], Value)
