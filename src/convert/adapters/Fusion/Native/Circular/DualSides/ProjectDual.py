from convert.adapters.Fusion.Native.Circular.DualSides.CheckDualLive import (
    CheckDualLive,
)
from convert.adapters.Fusion.Native.Circular.DualSides.ProjectDualBody import (
    ProjectDualBody,
)
from convert.adapters.Fusion.Native.Circular.DualSides.ReadDualParams import (
    ReadDualParams,
)
from convert.adapters.Fusion.Native.Circular.DualSnapshots.CheckDualSnaps import (
    CheckDualSnaps,
)
from convert.adapters.Fusion.Native.Circular.ProjectCircle import CircleSketch
from convert.adapters.Fusion.Native.Circular.ReadCircle import ReadCircle
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Policy.CheckAuxiliary import CheckSceneRefs
from convert.adapters.Fusion.Native.Policy.CheckGraph import CheckGraph
from convert.adapters.Fusion.Native.Policy.CheckScopes import CheckScopes
from convert.adapters.Fusion.Native.Projection.ProjectRectangle import ProjectFeatures
from convert.adapters.Fusion.Native.Projection.ReadMaterial import ReadMaterial
from convert.adapters.Fusion.Native.Rectangle.CheckRegion import CheckRegion
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.DistanceValues import GetDistValues
from interchange.Features.FeatureDistExt import DistanceExtrude
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.geometry.Models.Transform import Transform
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordSource import CadSource


# strict projection requires full native identity and saved state before exposing both tapers
def ProjectDual(
    Model: DocumentModel, Source: CadSource, Graph: NativeGraph, Context: ExtrudeContext
) -> CadDocument:
    CheckGraph(Graph, Context)
    CheckScopes(Graph, Context, Model.Asset.AssetId)
    Shape = ReadCircle(Graph, Context)
    Parameters = ReadDualParams(Graph, Context)
    CheckRegion(Graph, Context, (Shape.CurveNode,), Model.Asset.AssetId)
    Features = ProjectFeatures(Graph, Context)
    Definition = Features[-1].definition
    if (
        not isinstance(Definition, DistanceExtrude)
        or Definition.SideMode != "two_sided"
    ):
        raise ValueError("Native circular draft requires independent distance sides")
    Values = GetDistValues(
        Features[-1], Definition, {Value.id: Value for Value in Parameters}
    )
    if Values.SecondTaperRadians is None:
        raise ValueError("Native circular draft requires a second taper owner")
    State = CheckDualLive(
        Graph,
        Context,
        Model,
        Shape,
        Values.UpperMm,
        -Values.LowerMm,
        Values.TaperRadians,
        Values.SecondTaperRadians,
    )
    CheckDualSnaps(Model, Graph, Context, Shape, State)
    CheckSceneRefs(Graph, Model.Graphics)
    Material = ReadMaterial(Graph, Context, Model)
    Geometry, BodyValue = ProjectDualBody(Context, Shape.Geometry, Values, Material.id)
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
        metadata={"fusion.read_only": True},
    )
    Document.AssertValid()
    return Document
