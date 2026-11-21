from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
from convert.adapters.solidworks.Archive.Bodies.RequireHistRef import RequireHistRef
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Reading.ReadGraphNode import ReadNodeMut

# archive member 8a0 qualifies the history pointer while its child is read
KHistReadFlag = "history_component_read"


# the native loader restores its clear history state after the pointer read
def ReadHistRefMut(FrameValue: ReadFrame) -> ArchiveNode:
    FlagsValue = FrameValue.ContextValue.FlagsValue
    PriorValue = FlagsValue.get(KHistReadFlag)
    if PriorValue not in (None, 0):
        raise BodyUnsupported("history component read context must be clear")
    FlagsValue[KHistReadFlag] = 1
    try:
        return RequireHistRef(ReadNodeMut(FrameValue.ReaderValue))
    finally:
        if PriorValue is None:
            _ = FlagsValue.pop(KHistReadFlag, None)
        else:
            FlagsValue[KHistReadFlag] = PriorValue
