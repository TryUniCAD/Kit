from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Parameters.ReadParameters import ReadParameters
from convert.adapters.Fusion.Native.Policy.CheckAuxiliary import CheckAuxiliary
from convert.adapters.Fusion.Native.Policy.CheckScopes import CheckScopes
from convert.adapters.Fusion.Native.Policy.CheckMassCache import CheckMassCache
from convert.adapters.Fusion.Native.Policy.CheckGraph import (
    CheckGraph,
    CheckShape,
)
from convert.adapters.Fusion.Native.Projection.ProjectRectangle import (
    ProjectBody,
    ProjectFeatures,
    ProjectSketch,
)
from convert.adapters.Fusion.Native.Projection.ReadMaterial import ReadMaterial
from convert.adapters.Fusion.Native.Rectangle.CheckBodyJoins import CheckBodyJoins
from convert.adapters.Fusion.Native.Rectangle.CheckOperations import CheckOperations
from convert.adapters.Fusion.Native.Rectangle.CheckRegion import CheckRegion
from convert.adapters.Fusion.Native.Rectangle.CheckPrismTags import CheckPrismTags
from convert.adapters.Fusion.Native.Rectangle.ReadRectangle import ReadRectangle
from convert.adapters.Fusion.Native.Rectangle.SelectRectangle import SelectRectangle
from convert.adapters.Fusion.State.EncodeState import EncodeState
from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from interchange.document.models.DocumentModel import CadDocument
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.geometry.models.Transform import Transform
from interchange.records.RecordConfig import Configuration
from interchange.records.RecordSource import CadSource


def ProjectVendor(Model: DocumentModel, Source: CadSource) -> CadDocument:
    if Model.Meshes or not (
        Model.Graphics is not None or Model.Snapshots or Model.Configurations
    ):
        raise ValueError(
            "Native-state version 2 requires the qualified auxiliary-bearing solid profile"
        )
    Graph = BuildGraph(Model)
    Context = SelectRectangle(Graph)
    CheckGraph(Graph, Context)
    CheckScopes(Graph, Context, Model.Asset.AssetId)
    Shape = ReadRectangle(Graph, Context)
    Parameters = ReadParameters(Graph, Context)
    CheckRegion(Graph, Context, Shape, Model.Asset.AssetId)
    History = CheckBodyJoins(Graph, Context, Model)
    CheckOperations(Graph, Context, History)
    CheckPrismTags(Graph, Context, Shape, History)
    CheckShape(Context, Shape, History)
    CheckMassCache(Context, History)
    CheckAuxiliary(Graph, Model, History)
    Material = ReadMaterial(Graph, Context, Model)
    Geometry, BodyValue = ProjectBody(Context, Shape, Material.id)
    Title = dict(Model.Asset.Properties).get("documentName", "")
    Document = CadDocument(
        Source,
        (Configuration("default", Title, True),),
        Parameters,
        (SupportPlane(Context.Plane.Identity, "XY", Transform()),),
        (ProjectSketch(Context, Shape),),
        (),
        ProjectFeatures(Graph, Context),
        (BodyValue,),
        brep=Geometry,
        materials=(Material,),
        metadata={"fusion.native_state": {"version": 2, "model": EncodeState(Model)}},
    )
    Document.AssertValid()
    return Document
