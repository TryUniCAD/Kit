from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.ReadBodyMut import ReadBodyMut
from convert.adapters.solidworks.Archive.CmgrHeader.ManagerSchemas import (
    KConfigHdrClass,
    KManagerClass,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader


# only the root can open a directory body while configuration headers are leaf bodies
def ReadMgrNodeMut(
    ContextValue: BodyContext, ReaderValue: GraphReader, NodeValue: ArchiveNode
) -> None:
    DepthValue = ReaderValue.NestingDepth
    Expected = KManagerClass if DepthValue == 1 else KConfigHdrClass
    if DepthValue not in (1, 2) or NodeValue.ClassValue != Expected:
        raise BodyUnsupported(
            f"SOLIDWORKS manager directory expected {Expected.NameValue} "
            + f"schema {Expected.SchemaValue} before reading its body"
        )
    ReadBodyMut(ContextValue, ReaderValue, NodeValue)
