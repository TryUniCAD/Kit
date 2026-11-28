from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Native import NativeFeature
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.CheckBareOwner import (
    CheckBareOwner,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.Cylinder.ReadLocalCyl import (
    ReadLocalCyl,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadLocalPayload import (
    CheckSoleGroup,
)
from interchange.brep.Topology.BrepModel import BrepModel


# both read modes must validate the same annular local body owner and physical history
def ReadAnnBody(
    NodesValue: Mapping[int, XmtNode],
    OffsetsValue: Mapping[int, int],
    Archive: SldprtArchive,
    OwnerValue: NativeFeature,
    GroupKey: str,
    MarkValue: int,
    PriorMark: int,
) -> BrepModel:
    CheckSoleGroup(Archive, "local annulus")
    CheckBareOwner(Archive, OwnerValue, GroupKey, MarkValue, PriorMark, "local annulus")
    return ReadLocalCyl(NodesValue, OffsetsValue)
