from hashlib import sha256 as HashBytes

from convert.adapters.Fusion.Native.Circular.CircleShape import CircleShape
from convert.adapters.Fusion.Native.Circular.ReadCircle import ReadCircle
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from tests.Convert.Integration.Fusion.DualSide.DualCase import DualCase


# archive hashing and ordinary decoding keep identity tests at the actual native boundary
def ReadTagSample(
    Sample: DualCase,
) -> tuple[DocumentModel, NativeGraph, ExtrudeContext, CircleShape]:
    Payload = Sample.Source.read_bytes()
    if HashBytes(Payload).hexdigest() != Sample.Digest:
        raise ValueError("Native tag source hash differs from its recorded sample")
    Model = ReadDocument(Payload)
    Graph = BuildGraph(Model)
    Context = SelectExtrusion(Graph)
    return Model, Graph, Context, ReadCircle(Graph, Context)
