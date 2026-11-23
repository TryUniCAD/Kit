from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Native import NativeFeature
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.CheckBareOwner import (
    CheckBareOwner,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadLocalPayload import (
    CheckSoleGroup,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadLocalPlane import (
    ReadLocalPlane,
)
from interchange.brep.Topology.BrepModel import BrepModel


# the single loop and periodic paths must retain their own validation contracts
def HasPocketLoops(NodesValue: Mapping[int, XmtNode]) -> bool:
    return not any(
        Value.KindValue in (31, 51) for Value in NodesValue.values()
    ) and any(
        Value.KindValue == 15 and Value.Integer("next") for Value in NodesValue.values()
    )


# both reader modes must bind the same local pocket through its actual producer
def ReadPocketBody(
    NodesValue: Mapping[int, XmtNode],
    OffsetsValue: Mapping[int, int],
    Archive: SldprtArchive,
    OwnerValue: NativeFeature,
    MarkValue: int,
    PriorMark: int,
) -> BrepModel:
    CheckSoleGroup(Archive, "local pocket")
    CheckBareOwner(
        Archive, OwnerValue, OwnerValue.name, MarkValue, PriorMark, "local pocket"
    )
    return ReadLocalPlane(NodesValue, OffsetsValue, AllowPocket=True)
