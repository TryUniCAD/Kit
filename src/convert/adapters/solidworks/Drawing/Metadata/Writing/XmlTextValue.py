# generated property names and values must remain valid xml before any native file can be published
def XmlTextValue(Value: object, AllowEmpty: bool) -> str:
    if not isinstance(Value, str) or (not Value and not AllowEmpty):
        raise ValueError("drawing metadata requires explicit xml text")
    if any(
        not (
            CodeValue in (9, 10, 13)
            or 32 <= CodeValue <= 55295
            or 57344 <= CodeValue <= 65533
            or 65536 <= CodeValue <= 1114111
        )
        for CodeValue in map(ord, Value)
    ):
        raise ValueError("drawing metadata text contains an invalid xml character")
    return Value
