from collections.abc import Sequence


# declared unicode values contain utf16 code units whose surrogate pairs must be preserved exactly
def ReadWideName(UnitsValue: Sequence[int]) -> str:
    if not UnitsValue or any(
        type(UnitValue) is not int or not 0 < UnitValue <= 0xFFFF
        for UnitValue in UnitsValue
    ):
        raise ValueError("native body name has invalid wide code units")
    BytesValue = b"".join(UnitValue.to_bytes(2, "little") for UnitValue in UnitsValue)
    NameValue = BytesValue.decode("utf-16-le")
    if not NameValue.isprintable() or NameValue.encode("utf-16-le") != BytesValue:
        raise ValueError("native body name has unqualified wide text")
    return NameValue
