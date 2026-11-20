from convert.adapters.solidworks.Archive.Bodies.IsBranchTaken import IsBranchTaken
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame


# selected native branches must keep the parent scope for later scalar and object fields
def ReadBranchMut(FrameValue: ReadFrame, RuleValue: NativeField) -> None:
    Selected = IsBranchTaken(FrameValue.ContextValue, FrameValue.ScopeValue, RuleValue)
    FrameValue.FieldsReader(
        FrameValue, RuleValue.BodyValue if Selected else RuleValue.OtherValue
    )
