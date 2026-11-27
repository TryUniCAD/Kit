from collections.abc import Mapping
from typing import cast as CastValue


# embedded typed records need explicit mapping validation before semantic fields are consumed
def NativeRecord(RecordValue: object) -> Mapping[str, object]:
    if not isinstance(RecordValue, Mapping):
        raise ValueError("typed model expected an embedded record")
    return CastValue(Mapping[str, object], RecordValue)
