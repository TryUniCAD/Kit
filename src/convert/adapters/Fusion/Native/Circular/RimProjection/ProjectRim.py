from convert.adapters.Fusion.Native.Circular.ProjectCircle import CircleSketch
from convert.adapters.Fusion.Native.Circular.ReadCircle import ReadCircle
from convert.adapters.Fusion.Native.Circular.RimFillet.CheckRimLive import CheckRimLive
from convert.adapters.Fusion.Native.Circular.RimFillet.CheckRimSnaps import (
    CheckRimSnaps,
)
from convert.adapters.Fusion.Native.Circular.RimPolicy.CheckRimPolicy import (
    CheckRimPolicy,
)
from convert.adapters.Fusion.Native.Circular.RimPolicy.ReadRimContext import (
    ReadRimContext,
)
from convert.adapters.Fusion.Native.Circular.RimPolicy.ReadRimParams import (
    ReadRimParams,
)
from convert.adapters.Fusion.Native.Circular.RimProjection.ProjectRimBody import (
    ProjectRimBody,
)
from convert.adapters.Fusion.Native.Circular.RimProjection.ProjectRimSteps import (
    ProjectRimSteps,
)
from convert.adapters.Fusion.Native.Circular.RimProjection.RimSelection import (
    RimSelection,
)
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Policy.CheckAuxiliary import CheckSceneRefs
from convert.adapters.Fusion.Native.Projection.ReadMaterial import ReadMaterial
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.DistanceValues import GetDistValues
from interchange.Features.FeatureDistExt import DistanceExtrude
from interchange.Features.Fillets.GetFilletVals import GetFilletVals
from interchange.Features.Fillets.RadiusFillet import RadiusFillet
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.geometry.Models.Transform import KTransformIdentity
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordSource import CadSource


# strict fillet inspection needs complete source ownership and saved geometry before neutral admission
def ProjectRim(
    Model: DocumentModel, Source: CadSource, Graph: NativeGraph
) -> CadDocument:
    Context = ReadRimContext(Graph)
    CheckRimPolicy(Model, Graph, Context)
    Shape = ReadCircle(Graph, Context.Extrusion)
    Prior, _ = CheckRimLive(Model, Graph, Context, Shape)
    CheckRimSnaps(Model, Graph, Context, Shape, Prior)
    Parameters = ReadRimParams(Graph, Context)
    Features = ProjectRimSteps(Graph, Context, Parameters)
    SelectionValue = RimSelection(Context)
    ExtrudeDef, FilletDef = Features[1].definition, Features[2].definition
    if not isinstance(ExtrudeDef, DistanceExtrude) or not isinstance(
        FilletDef, RadiusFillet
    ):
        raise ValueError("Native rim lost its bound extrusion or fillet definition")
    ParamMap = {Value.id: Value for Value in Parameters}
    DepthSpan = GetDistValues(Features[1], ExtrudeDef, ParamMap)
    Fillet, _ = GetFilletVals(
        Features[2], FilletDef, ParamMap, {SelectionValue.id: SelectionValue}
    )
    if DepthSpan.LowerMm != 0 or DepthSpan.TaperRadians != 0:
        raise ValueError("Native rim requires a positive untapered profile-plane start")
    CheckSceneRefs(Graph, Model.Graphics)
    Material = ReadMaterial(Graph, Context.Extrusion, Model)
    Geometry, BodyValue = ProjectRimBody(
        Context, Shape.Geometry.radius, DepthSpan.UpperMm, Fillet, Material.id
    )
    Document = CadDocument(
        Source,
        (
            Configuration(
                "default", dict(Model.Asset.Properties).get("documentName", ""), True
            ),
        ),
        Parameters,
        (SupportPlane(Context.Extrusion.Plane.Identity, "XY", KTransformIdentity),),
        (CircleSketch(Context.Extrusion, Shape),),
        (SelectionValue,),
        Features,
        (BodyValue,),
        brep=Geometry,
        materials=(Material,),
        metadata={"fusion.read_only": True},
    )
    Document.AssertValid()
    return Document
