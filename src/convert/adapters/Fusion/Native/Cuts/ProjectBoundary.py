from convert.adapters.Fusion.Native.Cuts.SelectCutPair import SelectCutPair
from convert.adapters.Fusion.Native.Cuts.CheckCutGraph import CheckCutGraph
from convert.adapters.Fusion.Native.Cuts.ReadCutShapes import ReadCutShapes
from convert.adapters.Fusion.Native.Cuts.ReadCutParams import ReadCutParams
from convert.adapters.Fusion.Native.Cuts.ProjectCutSteps import ProjectCutSteps
from convert.adapters.Fusion.Native.Cuts.CutOutline import CutOutline
from convert.adapters.Fusion.Native.Cuts.CheckCutHistory import CheckCutHistory
from convert.adapters.Fusion.Native.Cuts.CheckCutMass import CheckCutMass
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.GraphValues import TextValue
from convert.adapters.Fusion.Native.Policy.CheckAuxiliary import CheckSceneRefs
from convert.adapters.Fusion.Native.Projection.ProjectRectangle import ProjectSketch
from convert.adapters.Fusion.Native.Projection.ReadMaterial import ReadMaterial
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.Geometry.Extrude.Polygon.PolygonExtrude import BuildPrism
from interchange.Features.DistanceValues import GetDistValues
from interchange.Features.FeatureDistExt import DistanceExtrude
from interchange.Features.Distance.DistanceCut import DistanceCut
from interchange.Features.Distance.GetCutValues import GetCutValues
from interchange.Features.FeatureBody import DesignBody
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.geometry.Models.Transform import Transform
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordTopology import TopologyCounts
from interchange.Records.RecordSource import CadSource


# complete bounded corner histories preserve editable operands without implying native writing acceptance
def ProjectBoundary(
    Model: DocumentModel, Source: CadSource, Graph: NativeGraph
) -> CadDocument:
    Contexts = SelectCutPair(Graph)
    BodyTag = CheckCutGraph(Graph, Contexts, Model.Asset.AssetId)
    Shapes = ReadCutShapes(Graph, Contexts, Model.Asset.AssetId)
    Parameters = ReadCutParams(Graph, Contexts)
    Features = ProjectCutSteps(Graph, Contexts)
    StockDef, CutDef = Features[1].definition, Features[3].definition
    if not isinstance(StockDef, DistanceExtrude) or not isinstance(CutDef, DistanceCut):
        raise ValueError("Native corner cut lost its editable distance definitions")
    ParamMap = {Value.id: Value for Value in Parameters}
    StockSpan = GetDistValues(Features[1], StockDef, ParamMap)
    CutSpan = GetCutValues(Features[3], CutDef, ParamMap)
    if (
        StockSpan.LowerMm != 0
        or CutSpan.LowerMm != 0
        or CutSpan.UpperMm < StockSpan.UpperMm
    ):
        raise ValueError("Native corner cut requires a full depth positive tool")
    Outline = CutOutline(*Shapes)
    Profile = tuple(
        LineGeometry(Point, Outline[(Index + 1) % len(Outline)])
        for Index, Point in enumerate(Outline)
    )
    Geometry, Volume, AreaValue, Bounds = BuildPrism(
        Contexts[0].BodyNode.Identity, Transform(), Profile, 0.0, StockSpan.UpperMm
    )
    CheckCutHistory(
        Graph,
        Contexts,
        Model,
        Shapes,
        Outline,
        (StockSpan.UpperMm, CutSpan.UpperMm),
        BodyTag,
    )
    CheckCutMass(Contexts[0], Shapes, StockSpan.UpperMm, Volume, AreaValue)
    CheckSceneRefs(Graph, Model.Graphics)
    Material = ReadMaterial(Graph, Contexts[0], Model)
    Counts = TopologyCounts(
        1,
        len(Geometry.shells),
        len(Geometry.faces),
        len(Geometry.edges),
        len(Geometry.vertices),
        Volume,
        AreaValue,
        Bounds,
        True,
    )
    BodyValue = DesignBody(
        Contexts[0].BodyNode.Identity,
        TextValue(Contexts[0].BodyNode.Fields["userName"]),
        Features[-1].id,
        Counts,
        Material.id,
        attributes={"creation_index": Contexts[0].BodyNode.Fields["creationIndex"]},
    )
    Title = dict(Model.Asset.Properties).get("documentName", "")
    Document = CadDocument(
        Source,
        (Configuration("default", Title, True),),
        Parameters,
        tuple(
            SupportPlane(Context.Plane.Identity, "XY", Transform())
            for Context in Contexts
        ),
        tuple(
            ProjectSketch(Context, Shape)
            for Context, Shape in zip(Contexts, Shapes, strict=True)
        ),
        (),
        Features,
        (BodyValue,),
        brep=Geometry,
        materials=(Material,),
        metadata={
            "fusion.read_only": True,
        },
    )
    Document.AssertValid()
    return Document
