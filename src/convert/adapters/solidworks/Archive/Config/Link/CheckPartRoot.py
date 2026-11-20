from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader

# the bounded configuration start belongs to the current part root
KPartRoot = RuntimeClass("moPart_c", 1)


# reject other root declarations before reading their model fields or binding aliases
def CheckPartRoot(ReaderValue: GraphReader, RootValue: ArchiveNode) -> None:
    if (
        RootValue.ClassValue != KPartRoot
        or RootValue.StartOffset != 0
        or RootValue.IndexValue != ReaderValue.MapValue.BaseValue + 1
        or ReaderValue.MapValue.CounterValue != ReaderValue.MapValue.BaseValue + 2
    ):
        raise BodyUnsupported("SOLIDWORKS configuration start requires a current part")
