from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader


# a tagged nested body belongs to a separate sheet metal profile
def NoMasterRef(ReaderValue: GraphReader, NodeValue: ArchiveNode) -> None:
    raise BodyUnsupported(
        f"unqualified SOLIDWORKS sheet metal master tagged body {NodeValue.ClassValue.NameValue!r} at {ReaderValue.Cursor.GetOffset()}"
    )
