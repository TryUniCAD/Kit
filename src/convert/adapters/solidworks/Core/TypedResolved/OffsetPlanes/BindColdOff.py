from collections.abc import Mapping
from dataclasses import replace as ReplaceValue

from convert.adapters.base.NativeEvidence import KRefSupportSource
from convert.adapters.solidworks.Archive.Cmgr.CmgrGraph import CmgrGraph
from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.Native import NativeDimension, NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Circles.CircleGeomPlan import (
    CircleGeomPlan,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.OffsetPlanes.CheckOffState import (
    CheckOffState,
)
from convert.adapters.solidworks.Core.TypedResolved.OffsetPlanes.ReadOffBoss import (
    ReadOffBoss,
)
from convert.adapters.solidworks.Core.TypedResolved.OffsetPlanes.ReadOffDatum import (
    ReadOffDatum,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName


# signed placement and driving distance must stay attached to the actual principal reference
def BindOffPlane(
    ModelValue: NativeModel,
    NodeValue: ArchiveNode,
    DatumId: int,
    FrameValue: PlaneFrame,
    Driver: NativeDimension,
    IsReversed: bool,
) -> NativeModel:
    OffsetId = NativeNodeId(NodeValue)
    OriginValue = tuple(Value * 1000.0 for Value in FrameValue.OriginValue)
    (Plane,) = (
        ItemValue for ItemValue in ModelValue.planes if ItemValue.object_id == OffsetId
    )
    (Feature,) = (
        ItemValue
        for ItemValue in ModelValue.features
        if ItemValue.object_id == OffsetId
    )
    if (
        Plane.principal
        or Plane.name != ReadNativeName(NodeValue)
        or Feature.name != Plane.name
        or Feature.kind != "Plane"
        or Plane.origin_mm != OriginValue
        or (Plane.u_axis, Plane.v_axis, Plane.normal)
        != (FrameValue.AxisU, FrameValue.AxisV, FrameValue.NormalValue)
    ):
        raise ValueError("offset plane public row differs from its typed owner")
    return ReplaceValue(
        ModelValue,
        sketches=tuple(
            ReplaceValue(
                SketchValue,
                support_source=KRefSupportSource,
                unframed_support_plane_id=None,
            )
            for SketchValue in ModelValue.sketches
        ),
        planes=tuple(
            (
                ReplaceValue(
                    ItemValue, reference_ids=(DatumId,), OffsetReversed=IsReversed
                )
                if ItemValue is Plane
                else ItemValue
            )
            for ItemValue in ModelValue.planes
        ),
        features=tuple(
            (
                ReplaceValue(
                    ItemValue, dimensions=(ReplaceValue(Driver, kind="offset"),)
                )
                if ItemValue is Feature
                else ItemValue
            )
            for ItemValue in ModelValue.features
        ),
    )


# portable history and analytic reconstruction share one admitted offset and boss graph
def BindColdOff(
    ModelValue: NativeModel,
    LinkValue: NativeLink,
    ManagerValue: CmgrGraph,
    Features: Mapping[int, ArchiveNode],
    NodeValue: ArchiveNode,
) -> tuple[NativeModel, CircleGeomPlan]:
    OffsetId = NativeNodeId(NodeValue)
    CheckOffState(ModelValue, LinkValue, ManagerValue, Features, OffsetId)
    Datum, FrameValue, Driver, IsReversed = ReadOffDatum(LinkValue, NodeValue, Features)
    DatumId = NativeNodeId(Datum)
    PlanValue = ReadOffBoss(
        ModelValue, LinkValue, Features, FrameValue, DatumId, OffsetId, Driver
    )
    return (
        BindOffPlane(
            ModelValue, NodeValue, DatumId, FrameValue, Driver.DepthValue, IsReversed
        ),
        PlanValue,
    )
