from collections.abc import Mapping
from math import isfinite as IsFinite

from convert.Geometry.Parasolid import KMissingParam
from convert.adapters.solidworks.Archive.Partition.LocalPrism.CheckBoxPlanes import (
    CheckBoxPlanes,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.HasBoxCorners import (
    HasBoxCorners,
)
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Native import NativeFeature
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.Local.ReadLocalLabel import (
    ReadLocalLabel,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.Local.ReadLocalOwner import (
    ReadLocalOwner,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyAttrs import (
    ReadBodyAttrs,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadLocalPlane import (
    ReadLocalPlane,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from interchange.brep.Topology.BrepModel import BrepModel


# saved local boxes retain one face tolerance and leave edge and vertex tolerances unassigned
def HasStoredBoxTol(NodesValue: Mapping[int, XmtNode]) -> bool:
    if not any(NodeValue.KindValue == 80 for NodeValue in NodesValue.values()):
        return False
    FacesValue, EdgesValue, VerticesValue = (
        tuple(
            NodeValue.FieldsValue["tolerance"]
            for NodeValue in NodesValue.values()
            if NodeValue.KindValue == KindValue
        )
        for KindValue in (14, 16, 18)
    )
    if (len(FacesValue), len(EdgesValue), len(VerticesValue)) != (6, 12, 8):
        return False
    First = FacesValue[0]
    return (
        type(First) is float
        and IsFinite(First)
        and First > 0.0
        and all(Value == First for Value in FacesValue)
        and all(Value == KMissingParam for Value in (*EdgesValue, *VerticesValue))
    )


# a saved toleranced box must join the physical solid and restored marks to the actual import
def ReadStoredBox(
    NodesValue: Mapping[int, XmtNode],
    OffsetsValue: Mapping[int, int],
    Archive: SldprtArchive,
    OwnerValue: NativeFeature | None,
    GroupKey: str,
    MarkValue: int,
    PriorMark: int,
) -> BrepModel:
    LinkValue = ReadNativeLink(Archive, 0)
    AtomValue, FeatureId = ReadLocalOwner(LinkValue, GroupKey, MarkValue)
    if OwnerValue is not None and (
        OwnerValue.object_id != FeatureId
        or OwnerValue.native_stream != LinkValue.StreamName
    ):
        raise ValueError("saved local box has a foreign feature")
    ModelValue = RequireNative(LinkValue.ConfigValue.RootValue, "moPart_c")
    Activation = RequireNative(ModelValue.FieldsValue.get("fe38"), "moPMarkRecord_c")
    if not 0 < PriorMark < MarkValue or Activation.FieldsValue.get("f18") != PriorMark:
        raise ValueError("saved local box has an unrelated rollback predecessor")
    BrepValue = ReadLocalPlane(
        NodesValue, OffsetsValue, AllowPocket=False, AllowStoredAttrs=True
    )
    if not HasBoxCorners(BrepValue):
        raise ValueError("saved local tolerance layout does not own a rectangular solid")
    CheckBoxPlanes(BrepValue)
    Attributes = ReadBodyAttrs(NodesValue, NodesValue[1])
    if not Attributes:
        raise ValueError("saved local box has no original kernel owner")
    _ = ReadLocalLabel(NodesValue, Attributes, AtomValue, FeatureId, GroupKey)
    return BrepValue
