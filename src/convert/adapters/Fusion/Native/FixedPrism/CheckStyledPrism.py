from convert.adapters.Fusion.Native.FixedPrism.CheckStyledMaterial import (
    CheckStyleMat,
)
from convert.adapters.Fusion.Native.FixedPrism.CheckStyledRecipe import (
    CheckStylePick,
)
from convert.adapters.Fusion.Native.FixedPrism.ReadStyledHistory import (
    ReadStyleBody,
)
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.GraphValues import NumberValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode
from convert.adapters.Fusion.Native.Rectangle.RectGeometry import RectGeometry
from convert.adapters.Fusion.Native.SignedPrism.CheckSignedOwners import CheckOwnTags
from convert.adapters.Fusion.Native.SignedPrism.CheckSignedTags import (
    CheckEdgeTags,
    CheckFaceTags,
    ReadFeatureTags,
    SelectedCurves,
)
from convert.Formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.Formats.Fusion.BrepCodec.Journal.Planar.MakeLiveTable import MakeLiveTable
from convert.Formats.Fusion.BrepCodec.Journal.Planar.PlanarShell import PlanarShell
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.Formats.Fusion.EntityCodec.Recipes.Model.RecipeValue import RecipeValue
from convert.Formats.Fusion.GeometryCodec.Prism.PrismLayout import KFaceCorners


# every stored face representation must resolve the same measured topological occurrence
def CheckStylePrism(
    Graph: NativeGraph,
    Context: ExtrudeContext,
    Model: DocumentModel,
    Shape: RectGeometry,
    Owner: NativeNode,
    MaterialTag: str,
    Recipe: RecipeValue,
) -> None:
    if len(Model.Bodies) != 1 or not isinstance(Model.Bodies[0].History, JournalModel):
        raise ValueError("Native face appearance requires one typed cuboid journal")
    History = Model.Bodies[0].History
    Normal = CheckStylePick(History, MaterialTag, Recipe)
    AxisIndex = next(Index for Index, Coordinate in enumerate(Normal) if Coordinate)
    AxisFlag = 1 << AxisIndex
    Upper = Normal[AxisIndex] > 0
    (FaceRole,) = tuple(
        Index
        for Index, Corners in enumerate(KFaceCorners)
        if all(bool(Corner & AxisFlag) == Upper for Corner in Corners)
    )
    Solid = ReadStyleBody(Graph, Context, Model, Shape, MaterialTag, FaceRole)
    CheckStyleOps(Graph, Context, Model, Shape, History, Solid)
    CheckStyleMat(Graph, Context, Model, History, Owner, Normal)


# the style operation does not replace the actual extrusion and its sketch edge owners
def CheckStyleOps(
    Graph: NativeGraph,
    Context: ExtrudeContext,
    Model: DocumentModel,
    Shape: RectGeometry,
    History: JournalModel,
    Solid: PlanarShell,
) -> None:
    Table = MakeLiveTable(History, Solid.StateId)
    FaceTags = ReadFeatureTags(Table)
    BodyTag = FaceTags.pop(Solid.BodyRef, None)
    if BodyTag is None:
        raise ValueError("Native styled cuboid has no extrusion body tag")
    Operation, Sides = CheckOwnTags(
        Graph, Context, Model, Shape, History, Solid, BodyTag
    )
    Height = NumberValue(Context.Along.Fields["value"])
    Curves = SelectedCurves(Shape, Native=True)
    _ = CheckFaceTags(Solid, FaceTags, Operation, Height, Sides, Curves)
    CheckEdgeTags(Table, Curves, Height, 2)
