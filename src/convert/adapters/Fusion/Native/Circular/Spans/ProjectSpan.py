from interchange.Features.FeatureDistExt import DistanceExtrude
from convert.adapters.Fusion.Native.Circular.ProjectCircle import CircleSketch
from convert.adapters.Fusion.Native.Circular.ReadCircle import ReadCircle
from convert.adapters.Fusion.Native.Circular.RotaryMass import RotaryMass
from convert.adapters.Fusion.Native.Circular.Spans.CheckSpanHist import (
    CheckSpanHist,
)
from convert.adapters.Fusion.Native.Graph.GraphValues import NumberValue, TextValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Parameters.ReadParameters import ReadParameters
from convert.adapters.Fusion.Native.Policy.CheckGraph import CheckGraph
from convert.adapters.Fusion.Native.Policy.CheckScopes import CheckScopes
from convert.adapters.Fusion.Native.Policy.CheckAuxiliary import CheckSceneRefs
from convert.adapters.Fusion.Native.Projection.ProjectRectangle import ProjectFeatures
from convert.adapters.Fusion.Native.Projection.ReadMaterial import ReadMaterial
from convert.adapters.Fusion.Native.Rectangle.CheckRegion import CheckRegion
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.Formats.Fusion.GeometryCodec.Frustum.FrustumBody import FrustumBody
from convert.Geometry.Extrude.Circular.CircularExtrude import BuildCircular
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.DistanceValues import GetDistValues
from interchange.Features.FeatureBody import DesignBody
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.geometry.Models.Transform import Transform
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordSource import CadSource
from interchange.Records.RecordTopology import TopologyCounts


# signed and centered circular solids retain editable extent roles alongside their actual saved geometry
def ProjectSpan(
    Model: DocumentModel, Source: CadSource, Graph: NativeGraph, Context: ExtrudeContext
) -> CadDocument:
    CheckGraph(Graph, Context)
    CheckScopes(Graph, Context, Model.Asset.AssetId)
    Shape = ReadCircle(Graph, Context)
    Parameters = ReadParameters(
        Graph, Context, Reverse=NumberValue(Context.Along.Fields["value"]) < 0
    )
    CheckRegion(Graph, Context, (Shape.CurveNode,), Model.Asset.AssetId)
    Features = ProjectFeatures(Graph, Context)
    Definition = Features[-1].definition
    if not isinstance(Definition, DistanceExtrude):
        raise ValueError("Native circular span requires a distance extrusion")
    Values = GetDistValues(
        Features[-1], Definition, {Value.id: Value for Value in Parameters}
    )
    if Values.TaperRadians != 0 or Values.SecondTaperRadians not in (None, 0):
        raise ValueError("Native circular span requires an untapered solid")
    Solid = FrustumBody(
        Shape.Geometry.radius,
        Shape.Geometry.radius,
        Values.UpperMm - Values.LowerMm,
        (Shape.Geometry.center.x, Shape.Geometry.center.y, Values.LowerMm),
    )
    CheckSpanHist(Graph, Context, Model, Shape, Solid)
    RotaryMass(Context, Solid)
    CheckSceneRefs(Graph, Model.Graphics)
    Material = ReadMaterial(Graph, Context, Model)
    Geometry, Volume, AreaValue, Bounds = BuildCircular(
        Context.BodyNode.Identity,
        Transform(),
        Shape.Geometry,
        Values.LowerMm,
        Values.UpperMm,
        Shape.Geometry.radius,
        Shape.Geometry.radius,
    )
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
        Context.BodyNode.Identity,
        TextValue(Context.BodyNode.Fields["userName"]),
        Context.Extrude.Identity,
        Counts,
        Material.id,
        attributes={"creation_index": Context.BodyNode.Fields["creationIndex"]},
    )
    Title = dict(Model.Asset.Properties).get("documentName", "")
    Document = CadDocument(
        Source,
        (Configuration("default", Title, True),),
        Parameters,
        (SupportPlane(Context.Plane.Identity, "XY", Transform()),),
        (CircleSketch(Context, Shape),),
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
