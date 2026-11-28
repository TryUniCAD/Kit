from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.WriteBodyMut import WriteBodyMut
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteNodeMut import WriteNodeMut
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Motion.MakeMotionGraph import MakeMotionGraph
from convert.adapters.solidworks.Archive.Motion.MotionLayouts import (
    KMotionLayouts,
    KMotionSchemas,
)
from convert.adapters.solidworks.Archive.Motion.MotionStudy import MotionStudy
from convert.adapters.solidworks.Archive.Scalars.EncodeScalar import EncodeScalar


# the title directory must follow an independently encoded manager and study object graph
def WriteMotionBody(StudyValue: MotionStudy) -> bytes:
    ContextValue = BodyContext(19000, KMotionLayouts, {}, KMotionSchemas)
    WriterValue = BodyWriter(ArchiveMaps(1), ContextValue, WriteBodyMut)
    WriteNodeMut(WriterValue, MakeMotionGraph(StudyValue))
    return EncodeScalar(19000, "u32") + bytes(WriterValue.OutputValue)
