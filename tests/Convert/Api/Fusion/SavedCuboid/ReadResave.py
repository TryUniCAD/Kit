from hashlib import sha256 as HashBytes
from pathlib import Path as FilePath

from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.GraphChecks import LinkedNodes, ResolveField
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel

# the pinned native edit keeps its capture identity across shared suite processes
KResaveDigest = "22128494045f7a9adb1e9eed7e1a95aeab06f067dea371c27981333b72d23968"


# repositories locate the tracked native control without relying on the test working directory
def ResavePath() -> FilePath:
    return (
        FilePath(__file__).resolve().parents[5]
        / "re/Fusion/LocalOracle/SavedCuboidRoundTrip/Controls/GeneratedResaveEdited.f3d"
    )


# a candidate must be the exact observed vendor save before its order counts as evidence
def ReadResave() -> bytes:
    Payload = ResavePath().read_bytes()
    assert HashBytes(Payload).hexdigest() == KResaveDigest
    return Payload


# source slots must follow the actual design table and catalog ownership links
def GetCatalog(Model: DocumentModel) -> tuple[NativeNode, NativeNode, tuple[int, ...]]:
    Graph = BuildGraph(Model)
    Table = Graph.OneClass("ParameterTable")
    Catalog = ResolveField(
        Graph, Table, "rParameterSearchByNameHelper", "ParameterSearchByNameHelper"
    )
    TableSlots = tuple(
        NodeValue.ObjectId for NodeValue in LinkedNodes(Graph, Table, "children")
    )
    return Table, Catalog, TableSlots
