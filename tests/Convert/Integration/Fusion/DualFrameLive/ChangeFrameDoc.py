from tests.Convert.Integration.Fusion.DualFrameLive.ChangeBodyFrame import (
    ChangeBodyFrame,
)
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.GraphChecks import ResolveField
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.adapters.Fusion.Native.Circular.DualFrames.CheckFrameRef import (
    CheckFrameRef,
)
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.Formats.Fusion.EntityCodec.Model.MatrixValue import MatrixValue
from tests.Convert.Api.Fusion.Native.ChangeNative import ChangeField


# actual native graph edits test selected frame ownership through the archive serializer
def ChangeFrameDoc(Model: DocumentModel, CaseName: str) -> DocumentModel:
    if CaseName == "body_transform":
        return ChangeBodyFrame(Model)
    Graph = BuildGraph(Model)
    Context = SelectExtrusion(Graph)
    Matrix, Reference, Datum = CheckFrameRef(Graph, Context)
    if CaseName in ("ucs_matrix", "definition_matrix", "occurrence_matrix"):
        Owner = (
            Context.Plane
            if CaseName == "ucs_matrix"
            else Matrix if CaseName == "definition_matrix" else Context.Sketch
        )
        FieldName = (
            "transform"
            if CaseName == "ucs_matrix"
            else (
                "matrix3d" if CaseName == "definition_matrix" else "occurrenceTransform"
            )
        )
        return ChangeField(
            Model,
            Owner.ObjectId,
            FieldName,
            (
                Matrix.Fields["matrix3d"]
                if CaseName == "occurrence_matrix"
                else MatrixValue(None)
            ),
        )
    if CaseName == "datum_name":
        return ChangeField(Model, Datum.ObjectId, "originName", "XY")
    if CaseName == "datum_origin":
        return ChangeField(Model, Datum.ObjectId, "isOrigin", False)
    if CaseName == "datum_owner":
        return ChangeField(
            Model, Datum.ObjectId, "rParent", Context.Component.Fields["rParent"]
        )
    if CaseName == "definition_owner":
        return ChangeField(Model, Matrix.ObjectId, "rParentFeature", None)
    if CaseName in ("definition_active", "definition_inferred"):
        return ChangeField(
            Model,
            Matrix.ObjectId,
            "isActive" if CaseName == "definition_active" else "isInferredXAxis",
            CaseName != "definition_active",
        )
    if CaseName == "reference_scope":
        return ChangeField(Model, Reference.ObjectId, "rScope", None)
    if CaseName in ("update_owner", "update_health"):
        Update = ResolveField(
            Graph, Reference, "rDynamicUpdateData", "DynamicUpdateData"
        )
        return ChangeField(
            Model,
            Update.ObjectId,
            "rOwnerNode" if CaseName == "update_owner" else "isBodyOK",
            None if CaseName == "update_owner" else False,
        )

    if CaseName == "instance_owner":
        Instance = Graph.OneClass("ComponentInstance")
        return ChangeField(Model, Instance.ObjectId, "rTargetComponent", None)
    raise ValueError("Unknown native frame corruption")
