from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.KernelShapes import KKernelShapes
from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# historical pointers must bind to actual nodes in the proper restored state
def CheckUndoGraph(NodesValue: Mapping[int, XmtNode]) -> None:
    _ = RequireXmt(NodesValue, 1, 101)
    if sum(NodeValue.KindValue == 101 for NodeValue in NodesValue.values()) != 1:
        raise ValueError("rollback graph requires one WORLD")
    for NodeValue in NodesValue.values():
        for FieldValue in KKernelShapes[NodeValue.KindValue].FieldsValue:
            if FieldValue.EncodingValue != "p":
                continue
            Indexes = (
                NodeValue.Indexes(FieldValue.NameValue)
                if FieldValue.CountValue
                else (NodeValue.Integer(FieldValue.NameValue),)
            )
            for IndexValue in filter(None, Indexes):
                if IndexValue not in NodesValue:
                    raise ValueError("rollback graph has an unresolved pointer owner")
                if FieldValue.PointerClass in KKernelShapes:
                    _ = RequireXmt(NodesValue, IndexValue, FieldValue.PointerClass)
