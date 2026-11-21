from convert.adapters.Fusion.Native.DraftedRectangle.CheckDraftMass import (
    CheckDraftMass,
)
from convert.adapters.Fusion.Native.DraftedRectangle.ReadDraftBody import ReadDraftBody
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.GraphValues import NumberValue, TextValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Parameters.ReadParameters import ReadParameters
from convert.adapters.Fusion.Native.Policy.CheckAuxiliary import CheckSceneRefs
from convert.adapters.Fusion.Native.Policy.CheckGraph import CheckGraph
from convert.adapters.Fusion.Native.Policy.CheckScopes import CheckScopes
from convert.adapters.Fusion.Native.Projection.ProjectRectangle import (
    ProjectFeatures,
    ProjectSketch,
)
from convert.adapters.Fusion.Native.Projection.ReadMaterial import ReadMaterial
from convert.adapters.Fusion.Native.Rectangle.CheckRegion import CheckRegion
from convert.adapters.Fusion.Native.Rectangle.ReadRectangle import ReadRectangle
from convert.adapters.Fusion.Native.Rectangle.ReadRectRules import ReadRectRules
from convert.adapters.Fusion.State.EncodeState import EncodeState
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.Geometry.Extrude.Polygon.DraftPrism import BuildDraft
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumUnits import UnitSystem
from interchange.Features.FeatureBody import DesignBody
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.geometry.Models.Transform import KTransformIdentity
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordSource import CadSource
from interchange.Records.RecordTopology import TopologyCounts


# nonzero rectangular taper retains the live driving angle after both physical geometry roles are independently checked
def ProjectDraft(
    Model: DocumentModel, Source: CadSource, Graph: NativeGraph, Context: ExtrudeContext
) -> CadDocument:
    Rectangle = ReadRectRules(Graph, Context, AllowTaper=True)
    if Rectangle is None:
        raise ValueError(
            "Native drafted rectangle requires its constrained sketch drivers"
        )
    CheckGraph(Graph, Context, Rectangle)
    CheckScopes(Graph, Context, Model.Asset.AssetId)
    Shape = ReadRectangle(Graph, Context, Rectangle)
    if any(Value != 0.0 for Value in Shape.BasePoint):
        raise ValueError("Native drafted rectangle requires its anchored XY profile")
    Parameters = ReadParameters(Graph, Context, AllowTaper=True, Rectangle=Rectangle)
    CheckRegion(Graph, Context, Shape.LineNodes, Model.Asset.AssetId)
    Geometry, Measures, Bounds = BuildDraft(
        Context.BodyNode.Identity,
        Shape.Width,
        Shape.Depth,
        NumberValue(Context.Along.Fields["value"]) * 10,
        NumberValue(Context.Taper.Fields["value"]),
    )
    ReadDraftBody(Graph, Context, Model, Shape, Geometry, Measures)
    CheckDraftMass(Context, Measures)
    CheckSceneRefs(Graph, Model.Graphics)
    Material = ReadMaterial(Graph, Context, Model)
    SolidBody = DesignBody(
        Context.BodyNode.Identity,
        TextValue(Context.BodyNode.Fields["userName"]),
        Context.Extrude.Identity,
        TopologyCounts(1, 1, 6, 12, 8, Measures.Volume, Measures.Area, Bounds, True),
        Material.id,
        attributes={"creation_index": Context.BodyNode.Fields["creationIndex"]},
    )
    Metadata: dict[str, object] = {
        "fusion.native_state": {"version": 2, "model": EncodeState(Model)},
        "fusion.read_only": True,
    }
    if Rectangle.DisplayUnit is UnitSystem.KInch:
        Metadata["source_display_units"] = Rectangle.DisplayUnit.value
    Document = CadDocument(
        Source,
        (
            Configuration(
                "default", dict(Model.Asset.Properties).get("documentName", ""), True
            ),
        ),
        Parameters,
        (SupportPlane(Context.Plane.Identity, "XY", KTransformIdentity),),
        (ProjectSketch(Context, Shape, Rectangle),),
        (),
        ProjectFeatures(Graph, Context, Rectangle),
        (SolidBody,),
        brep=Geometry,
        materials=(Material,),
        metadata=Metadata,
    )
    Document.AssertValid()
    return Document
