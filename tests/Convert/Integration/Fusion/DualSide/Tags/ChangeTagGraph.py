from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.GraphChecks import ResolveField
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from tests.Convert.Api.Fusion.Native.ChangeNative import ChangeField


# persisted graph corruptions must disagree with the actual owning body and history
def ChangeTagGraph(Model: DocumentModel, CaseName: str) -> DocumentModel:
    Graph = BuildGraph(Model)
    Context = SelectExtrusion(Graph)
    if CaseName == "body_uuid":
        return ChangeField(
            Model,
            Context.DcBody.ObjectId,
            "bodyUuid",
            "00000000-0000-0000-0000-000000000000",
        )
    if CaseName == "history_end":
        return ChangeField(Model, Context.Extrude.ObjectId, "endModelHS", 999)
    Manager = ResolveField(
        Graph, Context.Fragment, "rFeatureIdManager", "DcFeatureIdManager"
    )
    return ChangeField(Model, Manager.ObjectId, "rOwnerFragment", None)
