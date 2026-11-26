from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.ReadBodyMut import ReadBodyMut
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader

# empty property managers allow only the actual shallow ownership tree
KPropOwnerDepths = (
    ("moCusPropMgr_c",),
    ("moCusPropContainer_c",),
    ("moFilePropContainer_c", "moCutListPropContainer_c"),
)


# owner roles must qualify before recursion can open child fields
def ReadPropNodeMut(
    ContextValue: BodyContext, ReaderValue: GraphReader, NodeValue: ArchiveNode
) -> None:
    DepthValue = ReaderValue.NestingDepth
    if (
        not 1 <= DepthValue <= len(KPropOwnerDepths)
        or NodeValue.ClassValue.NameValue not in KPropOwnerDepths[DepthValue - 1]
    ):
        raise ValueError("part property manager has unsupported owner placement")
    ReadBodyMut(ContextValue, ReaderValue, NodeValue)
