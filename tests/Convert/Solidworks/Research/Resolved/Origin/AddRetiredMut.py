from collections.abc import MutableMapping
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows


# a synthetic deleted slot must shift every actual handle while its cached region preserves independently ordered live identities
def AddRetiredMut(SketchValue: ArchiveNode) -> None:
    FieldsValue = SketchValue.FieldsValue
    LineRows = NativeRows(FieldsValue["lines"])
    RetiredValue = dict(NativeRecord(LineRows[0]["line"]))
    RetiredValue.update({"f08": 0, "f0c": -1, "f54": 5, "fd0": 0, "f20": 0})
    SketchValue.FieldsValue["lines"] = ({"flags": 0, "line": RetiredValue}, *LineRows)
    SketchValue.FieldsValue["nlines"] = len(LineRows) + 1
    for PointRow in NativeRows(FieldsValue["points"])[:4]:
        PointValue = NativeRecord(PointRow["point"])
        for NameValue in ("h1", "h2"):
            HandleValue = ArchiveNode.RequireNode(PointValue[NameValue])
            HandleValue.FieldsValue["idx"] = (
                CastValue(int, HandleValue.FieldsValue["idx"]) + 1
            )
    Dimensions = NativeRecord(FieldsValue["dims"])
    for AxisRow in NativeRows(Dimensions["log_g1"]):
        LogicalValue = NativeRecord(AxisRow["d"])
        HandleValue = ArchiveNode.RequireNode(LogicalValue["h1"])
        HandleValue.FieldsValue["idx"] = (
            CastValue(int, HandleValue.FieldsValue["idx"]) + 1
        )
    BoundaryItems: list[MutableMapping[str, object]] = [
        {
            "o": ArchiveNode(
                RuntimeClass("sgLineHandle", 1),
                {"f08": 0, "idx": IndexValue, "f1c": -1},
            )
        }
        for IndexValue in (3, 1, 4, 2)
    ]
    RegionValue = ArchiveNode(
        RuntimeClass("moSketchRegion_c", 1),
        {
            "f08": ArchiveNode(
                RuntimeClass("suObList", 1), {"n": 4, "items": BoundaryItems}
            )
        },
    )
    ListValue = ArchiveNode.RequireNode(FieldsValue["f5d8"])
    ListValue.FieldsValue.update({"n": 1, "items": [{"o": RegionValue}]})
