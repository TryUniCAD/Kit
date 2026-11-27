from convert.adapters.Fusion.Native.Circular.CheckRoundTags import CheckRoundTags
from convert.adapters.Fusion.Native.Circular.CircleShape import CircleShape
from convert.adapters.Fusion.Native.Circular.Spans.CheckSpanOwners import (
    CheckSpanOwners,
)
from convert.adapters.Fusion.Native.Circular.Spans.ReadSpanBody import ReadSpanBody
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.GraphChecks import ResolveField
from convert.adapters.Fusion.Native.Graph.GraphValues import SeriesItems
from convert.adapters.Fusion.Native.Graph.IntegerValue import IntegerValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Rectangle.CurveTags import CurveTag
from convert.Formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.Formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag
from convert.Formats.Fusion.BrepCodec.Models.SketchLink import SketchLink
from convert.Formats.Fusion.BrepCodec.Models.TopologyTags import TopologyTags
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.Formats.Fusion.EntityCodec.Model.ValuePair import ValuePair


# actual allocator and progenitor relationships determine both side operations without fixed identifiers
def ReadDualOwners(
    Graph: NativeGraph,
    Context: ExtrudeContext,
    Model: DocumentModel,
    Shape: CircleShape,
    State: GeometryState,
) -> tuple[tuple[int, ...], str]:
    History = Model.Bodies[0].History
    if not isinstance(History, JournalModel):
        raise ValueError("Native dual sides require typed journal history")
    BodyValue, BodyTag = ReadSpanBody(State)
    Operations = CheckSpanOwners(Graph, Context, Model, History, BodyValue, BodyTag)
    if len(Operations) != 2 or len(set(Operations)) != 2:
        raise ValueError("Native dual sides require two distinct active operations")
    Table = ResolveField(Graph, Context.Extrude, "rProgenitorTable", "ProgenitorTable")
    Curves = tuple(
        Entry
        for Entry in SeriesItems(Table.Fields["ProgenitorTagVec"])
        if isinstance(Entry, ValuePair)
        and Graph.Resolve(Entry.First).ClassName == "SketchCurveProgenitor"
    )
    if len(Curves) != 1:
        raise ValueError("Native dual sides require one selected curve progenitor")
    Primary = str(IntegerValue(Curves[0].Second))
    Owned = (Operations[0],)
    TagSet = TopologyTags(
        FeatureTag(Primary, Owned),
        FeatureTag("2", Owned),
        FeatureTag("1", Owned),
        FeatureTag("-1", Owned),
        FeatureTag("-" + str(CurveTag(Shape.CurveNode)), Owned),
        SketchLink(CurveTag(Shape.CurveNode), 0, 0, 1, 1),
    )
    CheckRoundTags(Graph, Context, Shape, Operations[0], TagSet)
    return Operations, Primary
