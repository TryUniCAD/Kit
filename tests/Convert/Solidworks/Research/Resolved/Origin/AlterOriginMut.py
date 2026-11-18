from collections.abc import MutableMapping
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from tests.Convert.Solidworks.Research.Resolved.Origin.AlterFixMut import AlterFixMut
from tests.Convert.Solidworks.Research.Resolved.Origin.AlterRefMut import (
    AlterRefMut,
)
from tests.Convert.Solidworks.Research.Resolved.Origin.AlterRegionMut import (
    AlterRegionMut,
)


# distinct owner failures must remain serialized evidence rather than bypassing the public reader with direct helper assertions
def AlterOriginMut(
    SketchValue: ArchiveNode, OtherSketch: ArchiveNode, ModeValue: str
) -> None:
    PointsValue = NativeRows(SketchValue.FieldsValue["points"])
    PointValue = CastValue(MutableMapping[str, object], PointsValue[4]["point"])
    Dimensions = CastValue(MutableMapping[str, object], SketchValue.FieldsValue["dims"])
    Relation = CastValue(
        MutableMapping[str, object], NativeRows(Dimensions["log_g2"])[0]["d"]
    )
    if ModeValue in ("origin-suppressed", "origin-drive-mode"):
        AlterFixMut(OtherSketch, ModeValue)
    elif ModeValue in ("retired-region", "retired-referenced", "wrong-region"):
        AlterRegionMut(SketchValue, ModeValue)
    elif ModeValue == "external-index":
        ArchiveNode.RequireNode(Relation["h1"]).FieldsValue["idx"] = 0
    elif ModeValue == "local-index":
        ArchiveNode.RequireNode(Relation["h2"]).FieldsValue["idx"] = 1
    elif ModeValue == "point-kind":
        PointValue["fe4"] = 0
    elif ModeValue == "reference-count":
        PointValue["f20"] = 0
    elif ModeValue == "extra-relation":
        Dimensions["log_g2"] = [*NativeRows(Dimensions["log_g2"])] * 2
        Dimensions["nlog2"] = 2
    else:
        AlterRefMut(SketchValue, OtherSketch, ModeValue)
