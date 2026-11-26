from re import fullmatch as FullMatch


# a digest must have its canonical complete hexadecimal representation
def ReadMeasSha(Value: object) -> str:
    if type(Value) is not str or FullMatch(r"[0-9a-f]{64}", Value) is None:
        raise ValueError("native measurement requires a canonical SHA-256")
    return Value
