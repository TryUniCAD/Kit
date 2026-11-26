from re import fullmatch as FullMatch

from convert.adapters.solidworks.Core.NativeDimension import NativeDimension


# count declarations retain their integer value before binary ownership is proven
def CountValue(Dimension: NativeDimension) -> int | None:
    Printed = Dimension.source_text.strip()
    if FullMatch(r"[0-9]{1,10}", Printed) and 0 < int(Printed) < 2**32:
        return int(Printed)
    return None
