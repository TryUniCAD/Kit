from collections.abc import Mapping


# endpoint and handle escapes use different markers and must never share a guessed index namespace
def LineIndex(
    FieldsValue: Mapping[str, object],
    CompactName: str,
    ExtendedName: str,
    MarkerValue: int,
) -> int:
    CompactValue = FieldsValue.get(CompactName)
    if type(CompactValue) is not int or not 0 <= CompactValue <= MarkerValue:
        raise ValueError("typed line ring has an invalid compact index")
    Value = (
        FieldsValue.get(ExtendedName) if CompactValue == MarkerValue else CompactValue
    )
    if type(Value) is not int or Value < 0:
        raise ValueError("typed line ring has an invalid extended index")
    return Value
