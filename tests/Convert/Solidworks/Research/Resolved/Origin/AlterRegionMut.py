from collections.abc import MutableMapping
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from tests.Convert.Solidworks.Research.Resolved.Origin.AddRetiredMut import (
    AddRetiredMut,
)


# inactive line and region failures must keep distinct actual array references instead of renumbering them into accepted geometry
def AlterRegionMut(SketchValue: ArchiveNode, ModeValue: str) -> None:
    AddRetiredMut(SketchValue)
    if ModeValue == "retired-referenced":
        Dimensions = NativeRecord(SketchValue.FieldsValue["dims"])
        AxisValue = CastValue(
            MutableMapping[str, object], NativeRows(Dimensions["log_g1"])[0]["d"]
        )
        ArchiveNode.RequireNode(AxisValue["h1"]).FieldsValue["idx"] = 0
    elif ModeValue == "wrong-region":
        Regions = ArchiveNode.RequireNode(SketchValue.FieldsValue["f5d8"])
        Region = ArchiveNode.RequireNode(
            NativeRows(Regions.FieldsValue["items"])[0]["o"]
        )
        Boundary = ArchiveNode.RequireNode(Region.FieldsValue["f08"])
        Handle = ArchiveNode.RequireNode(
            NativeRows(Boundary.FieldsValue["items"])[0]["o"]
        )
        Handle.FieldsValue["idx"] = 0
    elif ModeValue != "retired-region":
        raise ValueError("unknown region graph mutation")
