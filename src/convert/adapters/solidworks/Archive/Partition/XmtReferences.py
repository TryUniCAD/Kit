from collections.abc import Iterator

from convert.adapters.solidworks.Archive.Partition.KernelShapes import KKernelShapes
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# every active pointer must resolve before a label can be bound to document geometry
def XmtReferences(NodeValue: XmtNode) -> Iterator[int]:
    for FieldValue in KKernelShapes[NodeValue.KindValue].FieldsValue:
        if FieldValue.EncodingValue != "p":
            continue
        if FieldValue.CountValue:
            yield from filter(None, NodeValue.Indexes(FieldValue.NameValue))
        elif IndexValue := NodeValue.Integer(FieldValue.NameValue):
            yield IndexValue
