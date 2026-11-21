from collections.abc import MutableMapping
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from tests.Convert.Solidworks.Research.Resolved.Lines.ExtendLineMut import ExtendLineMut
from tests.Convert.Solidworks.Research.Resolved.Lines.AlterOrderMut import (
    AlterOrderMut,
)
from tests.Convert.Solidworks.Research.Resolved.Lines.AlterIdsMut import AlterIdsMut


# serialized negative and identity controls must exercise real public reading without changing the original generated input
def ApplyLineMut(FieldsValue: MutableMapping[str, object], ModeValue: str) -> None:
    Points = CastValue(tuple[MutableMapping[str, object], ...], FieldsValue["points"])
    Lines = CastValue(tuple[MutableMapping[str, object], ...], FieldsValue["lines"])
    Point = CastValue(MutableMapping[str, object], Points[0]["point"])
    LineValue = CastValue(MutableMapping[str, object], Lines[0]["line"])
    if ModeValue == "bad-handle":
        Handle = CastValue(ArchiveNode, Point["h1"])
        Handle.FieldsValue["idx"] = 1
    elif ModeValue == "bad-endpoint":
        LineValue["fcc_s"] = len(Points)
    elif ModeValue == "construction":
        LineValue["f54"] = CastValue(int, LineValue["f54"]) | 1
    elif ModeValue == "duplicate-id":
        LineValue["f08"] = CastValue(MutableMapping[str, object], Lines[1]["line"])[
            "f08"
        ]
    elif ModeValue == "extended-encoding":
        ExtendLineMut(Point, LineValue)
    elif ModeValue == "reordered-lines":
        AlterOrderMut(Points, Lines, FieldsValue)
    elif ModeValue == "sparse-identities":
        AlterIdsMut(Points, Lines)
    elif ModeValue == "relation-owner":
        Dimensions = CastValue(MutableMapping[str, object], FieldsValue["dims"])
        Owner = CastValue(ArchiveNode, Dimensions["f118"])
        Owner.FieldsValue["n"] = 1
        Owner.FieldsValue["items"] = ({"o": Point["h1"]},)
    else:
        raise ValueError("unknown polygon archive mutation")
