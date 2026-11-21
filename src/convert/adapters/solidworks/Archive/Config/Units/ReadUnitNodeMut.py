from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.ReadBodyMut import ReadBodyMut
from convert.adapters.solidworks.Archive.Config.Units.UnitSchemas import (
    KUnitRowClasses,
    KUnitTableClass,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader


# only the measured table row and optional length roles can open new bodies
def ReadUnitNodeMut(
    ContextValue: BodyContext, ReaderValue: GraphReader, NodeValue: ArchiveNode
) -> None:
    DepthValue = ReaderValue.NestingDepth
    ClassValue = NodeValue.ClassValue
    if not (
        (DepthValue == 1 and ClassValue == KUnitTableClass)
        or (DepthValue == 2 and ClassValue in KUnitRowClasses)
        or (DepthValue == 3 and ClassValue == KUnitRowClasses[0])
    ):
        raise BodyUnsupported("SOLIDWORKS unit table has the wrong body owner role")
    ReadBodyMut(ContextValue, ReaderValue, NodeValue)
