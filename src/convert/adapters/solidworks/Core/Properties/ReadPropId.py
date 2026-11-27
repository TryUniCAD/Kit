from re import fullmatch as MatchName


# identifiers must preserve canonical nonnegative decimal ownership without aliases or reserved name collisions
def ReadPropId(TextValue: str | None) -> int:
    if TextValue is None or MatchName(r"0|[1-9][0-9]{0,9}", TextValue) is None:
        raise ValueError("part property identifier is not a canonical decimal value")
    IdentValue = int(TextValue)
    if IdentValue > 0x7FFFFFFF:
        raise ValueError("part property identifier exceeds its native signed range")
    return IdentValue
