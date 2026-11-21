from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.Owned.CheckOwnedNode import (
    CheckOwnedNode,
    GetOwnedClass,
)
from convert.adapters.solidworks.Archive.Bodies.Owned.CopyOwnedMap import CopyOwnedMap
from convert.adapters.solidworks.Archive.Bodies.ReadScopeValue import ReadScopeValue
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# direct emission keeps a refused body out of the surrounding bytes and identity map
def WriteOwnedMut(FrameValue: WriteFrame, RuleValue: NativeField) -> None:
    WriterValue = FrameValue.WriterValue
    ClassValue = GetOwnedClass(WriterValue.ContextValue, RuleValue)
    NodeValue = ArchiveNode.RequireNode(
        ReadScopeValue(FrameValue.ScopeValue, RuleValue.NameValue)
    )
    CheckOwnedNode(NodeValue, ClassValue, WriterValue.MapValue)
    LocalWriter = ReplaceValue(
        WriterValue,
        MapValue=CopyOwnedMap(WriterValue.MapValue),
        OutputValue=bytearray(),
    )
    ChildFrame = ReplaceValue(
        FrameValue,
        WriterValue=LocalWriter,
        ScopeValue=FieldScope(NodeValue.FieldsValue),
        NodeValue=NodeValue,
    )
    FrameValue.SchemaWriter(ChildFrame, ClassValue.NameValue)
    if (
        LocalWriter.MapValue.BaseValue != WriterValue.MapValue.BaseValue
        or LocalWriter.MapValue.Snapshot() != WriterValue.MapValue.Snapshot()
    ):
        raise ValueError(
            "SOLIDWORKS directly owned body may not change its archive map"
        )
    WriterValue.OutputValue.extend(LocalWriter.OutputValue)
