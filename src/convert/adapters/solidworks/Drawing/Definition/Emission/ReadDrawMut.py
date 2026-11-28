from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.ReadBodyMut import ReadBodyMut
from convert.adapters.solidworks.Archive.Header.HeaderClasses import KHeaderClasses
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader


# inline drawing header objects must share their surrounding model archive reader and identity map
def ReadDrawMut(
    ContextValue: BodyContext, ReaderValue: GraphReader, NodeValue: ArchiveNode
) -> None:
    ClassValue = NodeValue.ClassValue
    HeaderReader = (
        KHeaderClasses.get((ClassValue.NameValue, ClassValue.SchemaValue))
        if isinstance(ClassValue, RuntimeClass)
        else None
    )
    if HeaderReader is not None:
        ContextValue.UsageValue.SchemaCalls[ClassValue.NameValue] += 1
        HeaderReader(ReaderValue, NodeValue)
    else:
        ReadBodyMut(ContextValue, ReaderValue, NodeValue)
