from convert.Geometry.Parasolid import DecodePartData
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import (
    KLocalBodyStream,
    KPartitionStream,
)
from convert.adapters.solidworks.Container.SldprtFormat import SldprtFormat
from convert.adapters.solidworks.Core.Native import NativeFeature
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.Cylinder.CheckAnnGraph import (
    HasAnnularWalls,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.Cylinder.ReadAnnBody import (
    ReadAnnBody,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadLocalBodyNodes import (
    ReadLocalNodes,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadLocalEnvelope import (
    ReadLocalWrap,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadLocalPayload import (
    ReadLocalMarks,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadPocketBody import (
    HasPocketLoops,
    ReadPocketBody,
)
from interchange.brep.Topology.BrepModel import BrepModel


# the design view derives selected trimmed solid ownership without publishing geometry
def ReadTrimOnly(Archive: SldprtArchive, OwnerValue: NativeFeature) -> BrepModel | None:
    GroupData = Archive.get(KLocalBodyStream)
    if GroupData is None:
        return None
    try:
        Local = DecodePartData(GroupData, KLocalBodyStream)
        if len(Local) != 1 or Local[0].kind != "unknown":
            return None
        LocalData = Local[0].data
        NodesValue, OffsetsValue = ReadLocalNodes(LocalData, AllowPeriodic=True)
    except (KeyError, OverflowError, ValueError):
        return None
    Annular = HasAnnularWalls(NodesValue)
    if not Annular and not HasPocketLoops(NodesValue):
        return None
    try:
        GroupKey = ReadLocalWrap(GroupData, LocalData)
        if GroupKey != OwnerValue.name:
            raise ValueError("local body storage key differs from its resolved import")
        Profile = "local annulus" if Annular else "local pocket"
        MarkValue, PriorMark = ReadTrimMarks(Archive, Profile)
        if Annular:
            return ReadAnnBody(
                NodesValue,
                OffsetsValue,
                Archive,
                OwnerValue,
                GroupKey,
                MarkValue,
                PriorMark,
            )
        return ReadPocketBody(
            NodesValue, OffsetsValue, Archive, OwnerValue, MarkValue, PriorMark
        )
    except (KeyError, OverflowError, ValueError) as ErrorInfo:
        raise SldprtFormat(
            f"SLDPRT local geometry rejected: {ErrorInfo}"
        ) from ErrorInfo


# the trimmed view must still identify both physical parts of its local history
def ReadTrimMarks(Archive: SldprtArchive, Profile: str) -> tuple[int, int]:
    Physical = DecodePartData(Archive.require(KPartitionStream), KPartitionStream)
    if tuple(Value.kind for Value in Physical) != ("partition", "deltas"):
        raise ValueError(
            f"{Profile} requires the selected physical partition and deltas"
        )
    return ReadLocalMarks(Physical[0].data, Physical[1].data)
