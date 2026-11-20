from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.ReadBodyMut import ReadBodyMut
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader


# the selected member root must declare its expected class before reading any fields
def ReadMemBodyMut(
    ContextValue: BodyContext,
    MemberClass: RuntimeClass,
    ReaderValue: GraphReader,
    NodeValue: ArchiveNode,
) -> None:
    if ReaderValue.NestingDepth != 1 or NodeValue.ClassValue != MemberClass:
        raise BodyUnsupported(
            "SOLIDWORKS configuration member has an unsupported body owner"
        )
    ReadBodyMut(ContextValue, ReaderValue, NodeValue)
