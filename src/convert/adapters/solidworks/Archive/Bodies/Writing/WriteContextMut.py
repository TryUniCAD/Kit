from convert.adapters.solidworks.Archive.Bodies.ChangeContext import ChangeFlagsMut
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame


# graph writing advances the same byte free archive conditions as reading
def WriteContextMut(FrameValue: WriteFrame, RuleValue: NativeField) -> None:
    ChangeFlagsMut(FrameValue.WriterValue.ContextValue, RuleValue)
