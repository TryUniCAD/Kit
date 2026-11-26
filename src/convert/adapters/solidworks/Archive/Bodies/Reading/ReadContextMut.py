from convert.adapters.solidworks.Archive.Bodies.ChangeContext import ChangeFlagsMut
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame


# archive state changes must affect subsequent reads without consuming a wire field
def ReadContextMut(FrameValue: ReadFrame, RuleValue: NativeField) -> None:
    ChangeFlagsMut(FrameValue.ContextValue, RuleValue)
