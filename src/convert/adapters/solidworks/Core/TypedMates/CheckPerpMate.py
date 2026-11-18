from math import fsum as FloatSum
from math import isclose as IsClose

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadRows,
    RequireNode,
)
from convert.adapters.solidworks.Assembly.PlanarMates.PlanarContext import PlanarContext
from convert.adapters.solidworks.Assembly.PlanarMates.PlanarMate import PlanarMate
from convert.adapters.solidworks.Core.TypedMates.ReadFixedFlags import ReadFixedFlags
from convert.adapters.solidworks.Core.TypedMates.CheckPerpRefs import CheckPerpRefs
from convert.adapters.solidworks.Core.TypedMates.CheckPerpDatum import CheckPerpDatum


# perpendicular admission must retain its actual solved repeated child owners and independently orthogonal selected plane normals
def CheckPerpMate(
    PlanValue: PlanarMate, NodeValue: ArchiveNode, Context: PlanarContext
) -> None:
    if PlanValue.KindValue != "perpendicular":
        return
    Fields = NodeValue.FieldsValue
    FirstValue, SecondValue = PlanValue.Endpoints
    if (
        len(Context.OccurrenceMap) != 2
        or FirstValue.OccurrenceFeatureId == SecondValue.OccurrenceFeatureId
        or FirstValue.ChildDefinitionId != SecondValue.ChildDefinitionId
        or sum(Value["fixed"] is True for Value in ReadFixedFlags(Context)) != 1
        or PlanValue.AlignmentCode != 0
        or FieldInt(Fields, "f3b8") != 1
        or FieldInt(Fields, "f0c") != 0x100
        or Fields.get("f488") != ""
        or Fields.get("f490") != ""
    ):
        raise ValueError(
            "perpendicular mate is outside the solved repeated part profile"
        )
    ProductValue = FloatSum(
        First * Second
        for First, Second in zip(
            FirstValue.NormalValue, SecondValue.NormalValue, strict=True
        )
    )
    if not IsClose(ProductValue, 0.0, rel_tol=0.0, abs_tol=1e-10):
        raise ValueError("perpendicular selected plane normals are not orthogonal")
    CheckPerpRefs(NodeValue, Context.ModelNode)
    for Endpoint, RowValue in zip(
        PlanValue.Endpoints, ReadRows(Fields.get("f410")), strict=True
    ):
        CheckPerpDatum(
            Endpoint, RequireNode(RowValue.get("o"), "moPlaneRef_w"), Context
        )
