from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ValidateFields import ValidateFields
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame


# emitted conditional records must retain the same source proven ownership boundaries
def WriteValidMut(FrameValue: WriteFrame, RuleValue: NativeField) -> None:
    ValidateFields(
        FrameValue.WriterValue.ContextValue,
        FrameValue.ScopeValue,
        FrameValue.NodeValue,
        RuleValue.NameValue,
    )
