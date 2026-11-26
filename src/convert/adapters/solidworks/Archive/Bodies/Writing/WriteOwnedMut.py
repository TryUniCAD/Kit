from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadScopeValue import ReadScopeValue
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Bodies.RequirePartOwn import RequirePartOwn


# direct native ownership must serialize the actual typed object without adding a map entry
def WriteOwnedMut(FrameValue: WriteFrame, RuleValue: NativeField) -> None:
    NodeValue = ArchiveNode.RequireNode(
        ReadScopeValue(FrameValue.ScopeValue, RuleValue.NameValue)
    )
    ClassValue = RequirePartOwn(
        FrameValue.WriterValue.ContextValue, FrameValue.NodeValue, RuleValue
    )
    if NodeValue.ClassValue != ClassValue:
        raise ValueError("native directly owned object has the wrong class")
    ChildFrame = WriteFrame(
        FrameValue.WriterValue,
        FieldScope(NodeValue.FieldsValue),
        NodeValue,
        FrameValue.SchemaWriter,
        FrameValue.FieldsWriter,
    )
    FrameValue.SchemaWriter(ChildFrame, RuleValue.TypeValue)
