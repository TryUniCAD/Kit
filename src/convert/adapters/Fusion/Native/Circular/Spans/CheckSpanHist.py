from convert.adapters.Fusion.Native.Circular.CircleShape import CircleShape
from convert.adapters.Fusion.Native.Circular.CheckRoundBody import CheckRoundBody
from convert.adapters.Fusion.Native.Circular.CheckRoundTags import CheckRoundTags
from convert.adapters.Fusion.Native.Circular.Snapshots.CheckCoverage import (
    CheckCoverage,
)
from convert.adapters.Fusion.Native.Circular.Spans.CheckSpanOwners import (
    CheckSpanOwners,
)
from convert.adapters.Fusion.Native.Circular.Spans.CheckSpanSolid import CheckSpanSolid
from convert.adapters.Fusion.Native.Circular.Spans.CheckSpanTags import CheckSpanTags
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
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
from convert.Formats.Fusion.GeometryCodec.Frustum.FrustumBody import FrustumBody
from convert.adapters.Fusion.Native.Circular.Spans.ReadSpanState import ReadSpanState
from convert.adapters.Fusion.Native.Circular.Spans.ReadSpanBody import ReadSpanBody
from convert.adapters.Fusion.Native.Circular.Spans.CheckSpanSave import CheckSpanSave


# the active journal and saved snapshot must describe the same tagged editable cylinder
def CheckSpanHist(
    Graph: NativeGraph,
    Context: ExtrudeContext,
    Model: DocumentModel,
    Shape: CircleShape,
    Solid: FrustumBody,
) -> None:
    if len(Model.Bodies) != 1 or len(Model.Snapshots) != 1:
        raise ValueError("Native circular span requires one body history and snapshot")
    History = Model.Bodies[0].History
    Snapshot = Model.Snapshots[0].Snapshot
    if not isinstance(History, JournalModel) or not isinstance(Snapshot, GeometryState):
        raise ValueError("Native circular span requires typed journal geometry")
    State = ReadSpanState(Context, History, Solid)
    BodyValue, BodyTag = ReadSpanBody(State)
    Operations = CheckSpanOwners(Graph, Context, Model, History, BodyValue, BodyTag)
    CheckCoverage(State)
    CheckSpanSolid(State, BodyValue, Solid)
    Primary = CheckSpanTags(State, Context, Shape, Solid, Operations, True)
    Operation = Operations[0]
    MainOperation = (Operation,)
    TagSet = TopologyTags(
        FeatureTag(Primary, MainOperation),
        FeatureTag("2", MainOperation),
        FeatureTag("1", MainOperation),
        FeatureTag("-1", MainOperation),
        FeatureTag("-" + str(CurveTag(Shape.CurveNode)), MainOperation),
        SketchLink(CurveTag(Shape.CurveNode), 0, 0, 1, 1),
    )
    CheckRoundTags(Graph, Context, Shape, Operation, TagSet)
    if len(Operations) == 1:
        CheckRoundBody(Graph, Context, TagSet)
    CheckSpanSave(Snapshot, Context, Shape, Solid, Operations, Primary)
