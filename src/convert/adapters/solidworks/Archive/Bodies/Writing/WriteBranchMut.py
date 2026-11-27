from convert.adapters.solidworks.Archive.Bodies.IsBranchTaken import IsBranchTaken
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame


# the writer must select the same conditional fields as the native reader
def WriteBranchMut(FrameValue: WriteFrame, RuleValue: NativeField) -> None:
    Selected = IsBranchTaken(
        FrameValue.WriterValue.ContextValue,
        FrameValue.ScopeValue,
        RuleValue,
        FrameValue.NodeValue,
    )
    FrameValue.FieldsWriter(
        FrameValue, RuleValue.BodyValue if Selected else RuleValue.OtherValue
    )
