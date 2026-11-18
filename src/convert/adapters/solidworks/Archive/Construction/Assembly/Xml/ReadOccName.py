# canonical occurrence suffixes supply independent xml component number and basename while preserving the actual authored binary feature name
def ReadOccName(NameValue: str) -> tuple[str, str]:
    BaseValue, Separator, NumberValue = NameValue.rpartition("-")
    if (
        not BaseValue
        or not Separator
        or not NumberValue.isascii()
        or not NumberValue.isdecimal()
        or NumberValue.startswith("0")
        or len(NumberValue) > 10
        or not 1 <= int(NumberValue) <= 0x7FFFFFFF
    ):
        raise ValueError(
            "assembly occurrence requires a canonical positive decimal instance suffix"
        )
    return BaseValue, NumberValue
