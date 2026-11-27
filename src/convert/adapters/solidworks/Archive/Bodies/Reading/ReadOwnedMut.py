from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.Owned.CheckOwnedNode import (
    CheckOwnedNode,
    GetOwnedClass,
)
from convert.adapters.solidworks.Archive.Bodies.Owned.CopyOwnedMap import CopyOwnedMap
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
from convert.adapters.solidworks.Archive.Bodies.RequirePartOwn import RequirePartOwn
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Reading.ReadGraphNode import MakeArchiveNode


# untagged bodies consume their own fields before publishing the node and cursor
def ReadOwnedMut(FrameValue: ReadFrame, RuleValue: NativeField) -> None:
    ReaderValue = FrameValue.ReaderValue
    Factory = (
        MakeArchiveNode if ReaderValue.NodeFactory is None else ReaderValue.NodeFactory
    )
    ClassValue = RequirePartOwn(
        FrameValue.ContextValue, FrameValue.NodeValue, RuleValue
    )
    if RuleValue.TypeValue in FrameValue.ContextValue.SchemasValue:
        GetOwnedClass(FrameValue.ContextValue, RuleValue)
    NodeValue = ArchiveNode.RequireNode(Factory(ClassValue))
    CheckOwnedNode(NodeValue, ClassValue, ReaderValue.MapValue)
    if (
        NodeValue.FieldsValue
        or NodeValue.StartOffset is not None
        or NodeValue.EndOffset is not None
    ):
        raise ValueError("SOLIDWORKS directly owned read requires a fresh node")
    LocalReader = ReplaceValue(
        ReaderValue,
        Cursor=ReplaceValue(ReaderValue.Cursor),
        MapValue=CopyOwnedMap(ReaderValue.MapValue),
    )
    ChildFrame = ReplaceValue(
        FrameValue,
        ReaderValue=LocalReader,
        ScopeValue=FieldScope({}),
        NodeValue=NodeValue,
    )
    FrameValue.SchemaReader(ChildFrame, ClassValue.NameValue)
    if (
        LocalReader.MapValue.BaseValue != ReaderValue.MapValue.BaseValue
        or LocalReader.MapValue.Snapshot() != ReaderValue.MapValue.Snapshot()
    ):
        raise ValueError(
            "SOLIDWORKS directly owned body may not change its archive map"
        )
    NodeValue.FieldsValue.update(ChildFrame.ScopeValue.FieldsValue)
    NodeValue.StartOffset = ReaderValue.Cursor.GetOffset()
    EndOffset = LocalReader.Cursor.GetOffset()
    NodeValue.EndOffset = EndOffset
    ReaderValue.Cursor.OffsetValue = EndOffset
    FrameValue.ScopeValue.FieldsValue[RuleValue.NameValue] = NodeValue
