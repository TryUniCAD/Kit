from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader


# only open body callbacks contribute to the graph nesting depth
def ReadNodeBodyMut(ReaderValue: GraphReader, NodeValue: ArchiveNode) -> None:
    ReaderValue.NestingDepth += 1
    try:
        ReaderValue.BodyReader(ReaderValue, NodeValue)
    finally:
        ReaderValue.NestingDepth -= 1
