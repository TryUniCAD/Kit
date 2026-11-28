from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.ReadPlane import ReadVector
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.Patterns.MakeTiltPick import (
    MakeTiltPick,
)
from convert.adapters.solidworks.Core.TypedResolved.Patterns.TiltOwner import TiltOwner
from convert.adapters.solidworks.Core.TypedResolved.Patterns.TiltProjection import (
    TiltProjection,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from convert.adapters.solidworks.Core.TypedResolved.TypedProvenance import (
    TypedProvenance,
)
from interchange.Core.Common import FreezeMapping
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.Features.FeatureBoundPlane import BoundDatum
from interchange.Features.FeaturePlaneAxis import PlaneAxis
from interchange.Features.FeatureStep import FeatureStep
from interchange.Records.RecordParameter import Parameter, ParameterValue
from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.Selection import Selection
from interchange.geometry.Models.VectorSpace import SpaceVector


# the finite endpoints and ordered principal selections make the hinge directly portable
def BindTiltHinge(
    LinkValue: NativeLink, Hinge: FeatureStep, TiltValue: TiltOwner
) -> tuple[FeatureStep, tuple[Selection, Selection]]:
    AxisValue = RequireNative(
        TiltValue.HingeValue.FieldsValue.get("f700"), "moPlaneInterAxisData_c"
    )
    Fields = AxisValue.FieldsValue
    TopPick = MakeTiltPick(
        LinkValue,
        TiltValue.HingeValue,
        TiltValue.TopValue,
        RequireNative(Fields.get("f80"), "moPlaneRef_w"),
        "hinge-top-plane",
        True,
    )
    RightPick = MakeTiltPick(
        LinkValue,
        TiltValue.HingeValue,
        TiltValue.RightValue,
        RequireNative(Fields.get("f88"), "moPlaneRef_w"),
        "hinge-right-plane",
        True,
    )
    StartValue = SpaceVector(
        *(Value * 1000.0 for Value in ReadVector(Fields.get("f18")))
    )
    EndValue = SpaceVector(*(Value * 1000.0 for Value in ReadVector(Fields.get("f30"))))
    Definition = PlaneAxis(TopPick.id, RightPick.id, StartValue, EndValue)
    return (
        ReplaceValue(
            Hinge, definition=Definition, selection_ids=(TopPick.id, RightPick.id)
        ),
        (TopPick, RightPick),
    )


# a coincident hinge fixes the plane offset while the one actual angle remains driving
def BuildTiltModel(
    Document: CadDocument,
    LinkValue: NativeLink,
    Hinge: FeatureStep,
    Plane: FeatureStep,
    DatumNode: ArchiveNode,
    TiltValue: TiltOwner,
    AngleKey: str,
) -> TiltProjection:
    BoundHinge, HingePicks = BindTiltHinge(LinkValue, Hinge, TiltValue)
    DataValue = RequireNative(
        DatumNode.FieldsValue.get("f6f8"),
        "moConstraintCoincLineAtAnglePlaneRefplaneData_c",
    )
    Interface = RequireNative(
        DataValue.FieldsValue.get("f88"), "moConstraintRefplaneInterfaceData_c"
    )
    AngleValue = RequireNative(
        Interface.FieldsValue.get("f08"), "moRefPlaneAngleGeom_c"
    )
    LineValue = RequireNative(
        Interface.FieldsValue.get("f10"), "moRefPlaneCoincidentGeom_c"
    )
    BasePick = MakeTiltPick(
        LinkValue,
        DatumNode,
        TiltValue.RightValue,
        RequireNative(AngleValue.FieldsValue.get("f08"), "moPlaneRef_w"),
        "angular-base-plane",
        True,
    )
    HingePick = MakeTiltPick(
        LinkValue,
        DatumNode,
        TiltValue.HingeValue,
        RequireNative(LineValue.FieldsValue.get("f08"), "moLineRef_w"),
        "angular-hinge",
        False,
    )
    Frames = {Value.id: Value for Value in Document.support_planes}
    BaseValue = Frames[BasePick.path[0].entity_id]
    NativeId = NativeNodeId(DatumNode)
    Active = Frames[f"sldprt:plane:{NativeId}"]
    OffsetId = f"sldprt:parameter:{NativeId}:coincidence-offset"
    Offset = Parameter(
        id=OffsetId,
        name="Reference offset",
        value=ParameterValue(0.0, ValueKind.KLength, "mm"),
        role=ParameterRole.KDerived,
        owner_id=Plane.id,
        provenance=TypedProvenance(NativeNodeSpan(LinkValue, LineValue), OffsetId),
        attributes=FreezeMapping({"native_role": "through_origin_hinge_coincidence"}),
    )
    Support = ReplaceValue(
        Active, support_selection_id=BasePick.id, offset_parameter_id=OffsetId
    )
    Definition = BoundDatum(
        Support.id, AngleKey, OffsetId, "angle", BaseValue.transform
    )
    BoundPlane = ReplaceValue(
        Plane,
        definition=Definition,
        selection_ids=(BasePick.id, HingePick.id),
        parameter_ids=(AngleKey, OffsetId),
    )
    return TiltProjection(
        BoundHinge, BoundPlane, Support, (*HingePicks, BasePick, HingePick), Offset
    )
