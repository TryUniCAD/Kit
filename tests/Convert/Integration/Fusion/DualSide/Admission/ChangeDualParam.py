from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef
from tests.Convert.Api.Fusion.Native.ChangeNative import ChangeField


# corrupted independent roles must survive archive encoding before strict projection refuses them
def ChangeDualParam(Model: DocumentModel, ModeName: str) -> DocumentModel:
    Graph = BuildGraph(Model)
    Context = SelectExtrusion(Graph)
    Binding = Graph.Resolve(Context.Extrude.Fields["side2TaperAngle"])
    Parameter = Graph.Resolve(Binding.Fields["parameter"])
    if ModeName == "role":
        return ChangeField(Model, Parameter.ObjectId, "name", "TaperAngle")
    if ModeName == "unit":
        return ChangeField(Model, Parameter.ObjectId, "unit", "mm")
    if ModeName == "expression":
        return ChangeField(Model, Parameter.ObjectId, "expression", "1 + 1")
    if ModeName == "reciprocal":
        return ChangeField(
            Model, Parameter.ObjectId, "dcParameter", LocalRef(Context.Along.ObjectId)
        )
    if ModeName == "owner":
        return ChangeField(
            Model,
            Binding.ObjectId,
            "rrOwnerFeature",
            LocalRef(Context.SketchFeature.ObjectId),
        )
    if ModeName == "allocation":
        return ChangeField(
            Model, Binding.ObjectId, "rparamId", Context.Along.Fields["rparamId"]
        )
    if ModeName == "operation":
        return ChangeField(Model, Context.Extrude.ObjectId, "booleanOperation", 2)
    raise ValueError("Unknown native dual parameter corruption")
