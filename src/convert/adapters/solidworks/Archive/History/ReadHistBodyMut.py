from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.ReadBodyMut import ReadBodyMut
from convert.adapters.solidworks.Archive.History.HistoryTypes import (
    KDateHistClass,
    KHistoryRootTypes,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader


# the embedded version state may open a date code object but no extra metadata root
def ReadHistBodyMut(
    ContextValue: BodyContext, ReaderValue: GraphReader, NodeValue: ArchiveNode
) -> None:
    DepthValue = ReaderValue.NestingDepth
    if DepthValue == 1:
        IsAllowed = NodeValue.ClassValue in KHistoryRootTypes
    else:
        IsAllowed = DepthValue == 2 and NodeValue.ClassValue == KDateHistClass
    if not IsAllowed:
        raise BodyUnsupported("SOLIDWORKS history has an unsupported object role")
    ReadBodyMut(ContextValue, ReaderValue, NodeValue)
