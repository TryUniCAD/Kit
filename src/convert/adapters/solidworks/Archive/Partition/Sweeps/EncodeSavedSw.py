from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Partition.KernelShapes import KKernelShapes
from convert.adapters.solidworks.Archive.Partition.LocalWrite.GetXmtField import (
    GetXmtField,
)
from convert.adapters.solidworks.Archive.Partition.LocalWrite.LocalXmtProfile import (
    KLocalDescription,
)
from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.Sweeps.EncodeSweepXmt import (
    EncodeSwNodes,
)
from convert.adapters.solidworks.Archive.Partition.Sweeps.ReadSwSect import ReadSwSect
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from interchange.geometry.Models.GeometryCurves import CircleGeometry


# the retained next body identity is legal only on the standalone sheet root
def CheckSavedLinks(NodesValue: tuple[XmtNode, ...], IdsValue: set[int]) -> None:
    for NodeValue in NodesValue:
        for FieldValue in KKernelShapes[NodeValue.KindValue].FieldsValue:
            if FieldValue.EncodingValue != "p":
                continue
            Allowed = (
                {2}
                if NodeValue.IndexValue == 1 and FieldValue.NameValue == "next"
                else IdsValue
            )
            if any(
                type(Value) is not int or Value not in Allowed
                for Value in GetXmtField(NodeValue, FieldValue)[1]
            ):
                raise ValueError(
                    "saved sweep transmit contains a foreign resident link"
                )


# saved section replay keeps the measured resident order and validates its actual analytic circle
def EncodeSavedSw(NodesValue: object, CircleValue: CircleGeometry) -> bytes:
    if type(NodesValue) is not tuple or any(
        type(Value) is not XmtNode
        for Value in CastValue(tuple[object, ...], NodesValue)
    ):
        raise ValueError("saved sweep section requires typed resident cells")
    Nodes = CastValue(tuple[XmtNode, ...], NodesValue)
    IndexValue = {Value.IndexValue: Value for Value in Nodes}
    if not Nodes or Nodes[0].IndexValue != 1 or len(IndexValue) != len(Nodes):
        raise ValueError(
            "saved sweep section requires its distinct ordered resident cells"
        )
    if (
        ReadSwSect(IndexValue, RequireXmt(IndexValue, 1, 12), Embedded=True)
        != CircleValue
    ):
        raise ValueError("saved sweep section does not bind its actual circle")
    CheckSavedLinks(Nodes, {0, *IndexValue})
    return EncodeSwNodes(Nodes, KLocalDescription)
