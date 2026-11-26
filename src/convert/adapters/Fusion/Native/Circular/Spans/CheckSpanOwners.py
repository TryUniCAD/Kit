from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.Formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.adapters.Fusion.Native.Circular.Spans.CheckSpanStore import CheckSpanStore
from convert.adapters.Fusion.Native.Circular.Spans.ReadSpanOps import ReadSpanOps
from convert.adapters.Fusion.Native.Circular.Spans.ReadSpanProgen import ReadSpanProgen


# serialized identity allocation and geometry occurrences must all identify the same body
def CheckSpanOwners(
    Graph: NativeGraph,
    Context: ExtrudeContext,
    Model: DocumentModel,
    History: JournalModel,
    BodyValue: BodyNode,
    BodyTag: FeatureTag,
) -> tuple[int, ...]:
    CheckSpanStore(Graph, Context, Model, BodyValue)
    Operations = ReadSpanOps(Graph, Context, History, BodyValue, BodyTag)
    return ReadSpanProgen(Graph, Context, BodyTag, Operations)
