from collections.abc import Mapping, Sequence
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Blind.RequireEndNode import (
    RequireEndNode,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# fresh blind displays must retain exactly one local feature dimension instead of an external cache
def ReadEndHandle(DisplayValue: ArchiveNode) -> ArchiveNode:
    RowsValue = DisplayValue.FieldsValue["f850"]
    if not isinstance(RowsValue, (list, tuple)):
        raise ValueError("blind display requires an ordered handle collection")
    HandlesValue = CastValue(Sequence[object], RowsValue)
    if len(HandlesValue) != 1 or not isinstance(HandlesValue[0], Mapping):
        raise ValueError("blind display requires exactly one handle record")
    HandleRecord = CastValue(Mapping[str, object], HandlesValue[0])
    HandleValue = RequireEndNode(HandleRecord["o"], "moFeatureDimHandle_c")
    if (
        HandleValue.FieldsValue["fe8"] is not None
        or HandleValue.FieldsValue["f100"] is not None
    ):
        raise ValueError(
            "blind display requires a local dimension without an external cache"
        )
    return HandleValue
