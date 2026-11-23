from collections.abc import Sequence

from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KPartitionStream
from convert.adapters.solidworks.Core.Native import NativeFeature
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.Cylinder.CheckAnnGraph import (
    HasAnnularWalls,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.Cylinder.CheckCylOwner import (
    CheckCylOwner,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.Cylinder.ReadAnnBody import (
    ReadAnnBody,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.Cylinder.ReadLocalCyl import (
    ReadLocalCyl,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadLocalBodyNodes import (
    ReadLocalNodes,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadLocalEnvelope import (
    ReadLocalWrap,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadLocalPayload import (
    ReadLocalState,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadLocalPlane import (
    ReadLocalPlane,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadPocketBody import (
    HasPocketLoops,
    ReadPocketBody,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadStoredBox import (
    HasStoredBoxTol,
    ReadStoredBox,
)
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.Payloads.PayloadRecord import BrepPayload


# an empty active partition lets the single local solid supply its own complete boundary
def ReadLocalBrep(
    Payloads: Sequence[BrepPayload],
    GroupData: bytes,
    OwnerName: str,
    *,
    Archive: SldprtArchive | None = None,
    OwnerValue: NativeFeature | None = None,
) -> BrepModel:
    PartitionData = Archive.get(KPartitionStream) if Archive is not None else None
    LocalData, MarkValue, PriorMark = ReadLocalState(Payloads, PartitionData)
    if ReadLocalWrap(GroupData, LocalData) != OwnerName:
        raise ValueError("local body storage key differs from its resolved import")
    NodesValue, OffsetsValue = ReadLocalNodes(
        LocalData, AllowPeriodic=Archive is not None and OwnerValue is not None
    )
    if (
        Archive is not None
        and OwnerValue is not None
        and any(NodeValue.KindValue in (31, 51) for NodeValue in NodesValue.values())
    ):
        if PartitionData is None:
            raise ValueError("local cylinder has no physical active partition")
        if HasAnnularWalls(NodesValue):
            return ReadAnnBody(
                NodesValue,
                OffsetsValue,
                Archive,
                OwnerValue,
                OwnerName,
                MarkValue,
                PriorMark,
            )
        CheckCylOwner(Archive, OwnerValue, OwnerName, MarkValue, PriorMark)
        return ReadLocalCyl(NodesValue, OffsetsValue)
    if HasPocketLoops(NodesValue):
        if (
            Archive is None
            or OwnerValue is None
            or PartitionData is None
            or OwnerName != OwnerValue.name
        ):
            raise ValueError(
                "local pocket requires its exact feature and active partition"
            )
        return ReadPocketBody(
            NodesValue, OffsetsValue, Archive, OwnerValue, MarkValue, PriorMark
        )
    if (
        Archive is not None
        and PartitionData is not None
        and HasStoredBoxTol(NodesValue)
    ):
        return ReadStoredBox(
            NodesValue,
            OffsetsValue,
            Archive,
            OwnerValue,
            OwnerName,
            MarkValue,
            PriorMark,
        )
    return ReadLocalPlane(NodesValue, OffsetsValue, AllowPocket=False)
