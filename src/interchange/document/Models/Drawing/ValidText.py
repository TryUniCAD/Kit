from typing import cast as CastValue


# missing or malformed identifiers must be reported before graph lookups
def HasDrawingText(Value: object) -> bool:
    return isinstance(Value, str) and bool(Value.strip())


# repeated identifiers make sheet ownership and model links ambiguous
def HasUniqueIds(Values: tuple[object, ...]) -> bool:
    return all(HasDrawingText(Value) for Value in Values) and len(
        set(CastValue(tuple[str, ...], Values))
    ) == len(Values)
