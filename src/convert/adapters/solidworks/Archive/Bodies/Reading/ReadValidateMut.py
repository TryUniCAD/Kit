from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
from convert.adapters.solidworks.Archive.Bodies.ValidateFields import ValidateFields


# conditional native evidence must remain attached to the exact reached graph owner
def ReadValidMut(FrameValue: ReadFrame, RuleValue: NativeField) -> None:
    ValidateFields(
        FrameValue.ContextValue,
        FrameValue.ScopeValue,
        FrameValue.NodeValue,
        RuleValue.NameValue,
    )
