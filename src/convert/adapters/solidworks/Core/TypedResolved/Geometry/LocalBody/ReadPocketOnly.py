from convert.Geometry.Parasolid import DecodePartData
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import (
    KLocalBodyStream,
    KPartitionStream,
)
from convert.adapters.solidworks.Container.SldprtFormat import SldprtFormat
from convert.adapters.solidworks.Core.Native import NativeFeature
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


# the design view derives its pocket identity without publishing a geometry payload
def ReadPocketOnly(
    Archive: SldprtArchive, OwnerValue: NativeFeature
) -> BrepModel | None:
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
    if not HasPocketLoops(NodesValue):
        return None
    try:
        if ReadLocalWrap(GroupData, LocalData) != OwnerValue.name:
            raise ValueError("local body storage key differs from its resolved import")
        Physical = DecodePartData(Archive.require(KPartitionStream), KPartitionStream)
        if tuple(Value.kind for Value in Physical) != ("partition", "deltas"):
            raise ValueError(
                "local pocket requires the selected physical partition and deltas"
            )
        MarkValue, PriorMark = ReadLocalMarks(Physical[0].data, Physical[1].data)
        return ReadPocketBody(
            NodesValue, OffsetsValue, Archive, OwnerValue, MarkValue, PriorMark
        )
    except (KeyError, OverflowError, ValueError) as ErrorInfo:
        raise SldprtFormat(
            f"SLDPRT local geometry rejected: {ErrorInfo}"
        ) from ErrorInfo
