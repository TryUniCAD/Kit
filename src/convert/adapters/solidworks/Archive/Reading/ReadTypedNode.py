from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Archive.Reading.ReadGraphNode import ReadNodeMut


# references need type checks even when their object bytes were already decoded
def ReadTypedMut(
    ReaderValue: GraphReader, ClassName: str, *, AllowNull: bool = False
) -> ArchiveNode | None:
    NodeValue = ReadNodeMut(ReaderValue)
    if NodeValue is None and AllowNull:
        return None
    if NodeValue is None or NodeValue.ClassValue.NameValue != ClassName:
        raise ValueError(f"SOLIDWORKS archive expected {ClassName}")
    return NodeValue
