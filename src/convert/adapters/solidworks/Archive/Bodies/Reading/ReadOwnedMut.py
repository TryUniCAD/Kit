from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
from convert.adapters.solidworks.Archive.Bodies.RequirePartOwn import RequirePartOwn
from convert.adapters.solidworks.Archive.Reading.ReadGraphNode import MakeArchiveNode


# directly owned native objects have bodies and concrete identity without an archive allocation tag
def ReadOwnedMut(FrameValue: ReadFrame, RuleValue: NativeField) -> None:
    ReaderValue = FrameValue.ReaderValue
    Factory = (
        MakeArchiveNode if ReaderValue.NodeFactory is None else ReaderValue.NodeFactory
    )
    ClassValue = RequirePartOwn(
        FrameValue.ContextValue, FrameValue.NodeValue, RuleValue
    )
    NodeValue = Factory(ClassValue)
    ChildFrame = ReadFrame(
        FrameValue.ContextValue,
        ReaderValue,
        FieldScope(NodeValue.FieldsValue),
        NodeValue,
        FrameValue.SchemaReader,
        FrameValue.FieldsReader,
    )
    FrameValue.SchemaReader(ChildFrame, RuleValue.TypeValue)
    FrameValue.ScopeValue.FieldsValue[RuleValue.NameValue] = NodeValue
