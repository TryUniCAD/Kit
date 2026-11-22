from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.ReadBodyMut import ReadBodyMut
from convert.adapters.solidworks.Archive.Config.Link.CheckPartRoot import CheckPartRoot
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader


# the native root must be admitted before any configuration section fields execute
def ReadCfgBodyMut(
    ContextValue: BodyContext, ReaderValue: GraphReader, NodeValue: ArchiveNode
) -> None:
    if NodeValue.StartOffset == 0:
        CheckPartRoot(ReaderValue, NodeValue)
        ContextValue.PartRootValue = NodeValue
    ReadBodyMut(ContextValue, ReaderValue, NodeValue)
