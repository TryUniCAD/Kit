from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import (
    DatumTime,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyTree import (
    ReadBodyTree,
)
from convert.adapters.solidworks.Core.TypedResolved.Fillets.FilletHistory import (
    FilletHistory,
)
from convert.adapters.solidworks.Core.TypedResolved.Fillets.Saved.FilletEdge import (
    FilletEdge,
)
from convert.adapters.solidworks.Core.TypedResolved.Fillets.Saved.ReadFilletEnds import (
    ReadFilletEnds,
)
from convert.adapters.solidworks.Core.TypedResolved.Fillets.Saved.ReadFilletFace import (
    ReadFilletFace,
)
from convert.adapters.solidworks.Core.TypedResolved.Fillets.Saved.ReadFilletInc import (
    ReadFilletInc,
)
from convert.adapters.solidworks.Core.TypedResolved.Fillets.Saved.ReadFilletRef import (
    ReadFilletRef,
)
from convert.adapters.solidworks.Core.TypedResolved.Fillets.Saved.ReadFilletReps import (
    ReadFilletReps,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId


# the native support keys select one edge on the previously proved stock and its actual two endpoints
def JoinFilletEdge(History: FilletHistory, TopHeader: ArchiveNode) -> FilletEdge:
    Reference = ReadFilletRef(History)
    KeysValue = ReadFilletReps(History, Reference, TopHeader)
    NodesValue = History.StagesValue[1].NodesValue
    TreeValue = ReadBodyTree(NodesValue)
    StockId = NativeNodeId(History.OwnersValue.StockValue)
    StampValue = DatumTime(TopHeader, StockId)
    KeyFaces = {
        ReadFilletFace(NodesValue, FaceId, StockId, StampValue): FaceId
        for FaceId in TreeValue.FaceIds
    }
    if len(KeyFaces) != len(TreeValue.FaceIds):
        raise ValueError("saved fillet stock has ambiguous face identities")
    Faces = tuple(KeyFaces[KeyValue] for KeyValue in KeysValue)
    Edges = tuple(
        (EdgeId, First, Final)
        for EdgeId in TreeValue.EdgeIds
        for First, Final, Adjacent in (ReadFilletInc(NodesValue, EdgeId),)
        if Adjacent == frozenset(Faces[:2])
    )
    if len(Edges) != 1:
        raise ValueError("saved fillet did not select one actual preceding stock edge")
    ((EdgeId, First, Final),) = Edges
    EndpointPair = ReadFilletEnds(NodesValue, Faces, First, Final)
    return FilletEdge(Reference, EdgeId, Faces, EndpointPair)
