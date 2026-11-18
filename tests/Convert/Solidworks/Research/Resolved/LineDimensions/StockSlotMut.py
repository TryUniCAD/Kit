from collections.abc import MutableMapping
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows


# the ordinary reader must encounter a real sparse slot encoding through the complete serialized archive
def StockSlotMut(SketchValue: ArchiveNode, ModeValue: str) -> None:
    FieldsValue = SketchValue.FieldsValue
    Points = NativeRows(FieldsValue["points"])
    SlotsValue = (0, 2, 3, 4)
    for RowValue in Points:
        Point = CastValue(MutableMapping[str, object], RowValue["point"])
        Point["f20"] = 0
    Retired = dict(NativeRecord(Points[1]["point"]))
    Retired.update(
        {
            "f0c": 99 if ModeValue == "stock-retired-mark" else -1,
            "f54": 5,
            "fe8": 0,
            "h1": None,
            "h2": None,
        }
    )
    FieldsValue["npoints"] = len(Points) + 1
    FieldsValue["points"] = (Points[0], {"kind": 0, "point": Retired}, *Points[1:])
    Lines = NativeRows(FieldsValue["lines"])
    for RowValue in Lines:
        LineValue = CastValue(MutableMapping[str, object], RowValue["line"])
        for NameValue in ("fc8_s", "fcc_s"):
            LineValue[NameValue] = SlotsValue[CastValue(int, LineValue[NameValue])]
    if ModeValue == "stock-retired-endpoint":
        CastValue(MutableMapping[str, object], Lines[0]["line"])["fc8_s"] = 1
    Dimensions = CastValue(MutableMapping[str, object], FieldsValue["dims"])
    Dimensions.update({"ng2": 0, "val_g2": ()})
    Display = ArchiveNode.RequireNode(Dimensions["f118"])
    Display.FieldsValue.update({"n": 0, "items": ()})
