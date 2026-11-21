from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Reading.ReadGraphNode import MakeArchiveNode


# directly owned native objects have bodies and concrete identity without an archive allocation tag
def ReadOwnedMut(FrameValue: ReadFrame, RuleValue: NativeField) -> None:
    if RuleValue.TypeValue not in FrameValue.ContextValue.LayoutsValue:
        raise BodyUnsupported(
            f"unsupported SOLIDWORKS native field path {RuleValue.NameValue}"
        )
    ReaderValue = FrameValue.ReaderValue
    Factory = (
        MakeArchiveNode if ReaderValue.NodeFactory is None else ReaderValue.NodeFactory
    )
    NodeValue = Factory(RuntimeClass(RuleValue.TypeValue, 1))
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
