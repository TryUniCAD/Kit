from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.GraphChecks import ResolveField
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from tests.Convert.Api.Fusion.Native.ChangeNative import ChangeField


# a nonempty label and comment expose metadata loss even when the shape and dimensions match
def LabelSavedParam(Payload: bytes) -> bytes:
    Model = ReadDocument(Payload)
    Graph = BuildGraph(Model)
    Along = SelectExtrusion(Graph).Along
    Param = ResolveField(Graph, Along, "parameter", "Parameter")
    Changed = ChangeField(Model, Param.ObjectId, "name", "Extrusion height label")
    return EmitParsed(ChangeField(Changed, Param.ObjectId, "comment", "Shop note"))
