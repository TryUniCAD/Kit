from convert.adapters.Fusion.Native.Cuts.CheckStockTags import CheckStockTags
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.GraphChecks import ResolveField
from convert.adapters.Fusion.Native.Graph.GraphValues import SeriesItems
from convert.adapters.Fusion.Native.Graph.IntegerValue import IntegerValue
from convert.adapters.Fusion.Native.Rectangle.CheckSideRecipe import CheckSideRecipe
from convert.adapters.Fusion.Native.Rectangle.RectGeometry import RectGeometry
from convert.Formats.Fusion.EntityCodec.Model.ValuePair import ValuePair
from convert.Formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag


# side labels come from each feature profile recipe rather than the final geometric position alone
def CutSideLabels(
    Graph: NativeGraph,
    Context: ExtrudeContext,
    Shape: RectGeometry,
    Operation: int,
    Stock: bool,
) -> dict[int, FeatureTag]:
    Table = ResolveField(Graph, Context.Extrude, "rProgenitorTable", "ProgenitorTable")
    Entries = SeriesItems(Table.Fields["ProgenitorTagVec"])
    Labels: dict[int, FeatureTag] = {}
    BodyCount = 0
    for Entry in Entries:
        if not isinstance(Entry, ValuePair):
            raise ValueError("Native cut has a malformed progenitor entry")
        Progenitor = Graph.Resolve(Entry.First)
        if Progenitor.ClassName == "BodyProgenitor":
            BodyCount += 1
            continue
        if Progenitor.ClassName != "SketchCurveProgenitor":
            raise ValueError("Native cut has an unsupported progenitor role")
        Recipe = ResolveField(Graph, Progenitor, "rRecipe", "SketchCurveRecipe")
        TagId = CheckSideRecipe(Recipe.Fields["profileEdgeTagData"], Shape)
        if TagId in Labels:
            raise ValueError("Native cut repeats a sketch curve progenitor")
        Labels[TagId] = FeatureTag(str(IntegerValue(Entry.Second)), (Operation,))
    if (
        len(Labels) != 4
        or BodyCount != int(Stock)
        or IntegerValue(Table.Fields["tagId"])
        <= max(int(Value.PrimaryId) for Value in Labels.values())
    ):
        raise ValueError("Native cut progenitor coverage is incomplete")
    if Stock:
        CheckStockTags(Graph, Context, Labels, Operation)
    return Labels
