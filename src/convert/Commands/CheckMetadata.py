from collections.abc import Iterable, Mapping
from typing import cast as CastValue

KMetadataError = (
    "RetainedMetadata records are not conversion-ready; "
    "use kit decode or kit research for inspection"
)


def CheckMetadata(Metadata: Mapping[str, object]) -> None:
    Pending: list[object] = [Metadata]
    VisitedIds = set[int]()
    while Pending:
        Value = Pending.pop()
        ValueId = id(Value)
        if isinstance(Value, (bytes, bytearray, memoryview)) or (
            isinstance(Value, Mapping) and "solidworks_source_bytes" in Value
        ):
            raise ValueError(KMetadataError)
        if not isinstance(Value, (Mapping, list, tuple, set, frozenset)):
            continue
        if ValueId in VisitedIds:
            continue
        VisitedIds.add(ValueId)
        Pending.extend(
            CastValue(Mapping[object, object], Value).values()
            if isinstance(Value, Mapping)
            else CastValue(Iterable[object], Value)
        )
