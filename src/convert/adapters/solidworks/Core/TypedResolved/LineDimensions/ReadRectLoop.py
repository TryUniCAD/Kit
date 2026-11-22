from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.CheckDimGraph import (
    CheckDimGraph,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadLineDims import (
    ReadLineDims,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineLoop import LineLoop
from convert.adapters.solidworks.Core.TypedResolved.Lines.ReadLineLoop import (
    ReadLineLoop,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink


# the line loop may admit counted relations only after the actual driver graph provides their ownership
def ReadRectLoop(SketchValue: ArchiveNode, LinkValue: NativeLink) -> LineLoop:
    DimsValue = ReadLineDims(SketchValue, LinkValue)
    LoopValue = ReadLineLoop(SketchValue, LinkValue, DimsValue)
    CheckDimGraph(LoopValue, DimsValue)
    return LoopValue
