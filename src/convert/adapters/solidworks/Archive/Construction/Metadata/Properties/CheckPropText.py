# literal part properties need nonempty xml characters that survive native single line text edits
def CheckPropText(RawValue: object) -> str:
    if not isinstance(RawValue, str) or not RawValue:
        raise ValueError("ordinary part properties require nonempty text")
    if any(
        not (
            32 <= CodeValue <= 55295
            or 57344 <= CodeValue <= 65533
            or 65536 <= CodeValue <= 1114111
        )
        for CodeValue in map(ord, RawValue)
    ):
        raise ValueError("ordinary part properties require single-line XML text")
    return RawValue
