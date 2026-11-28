from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Partition.AttachedCylinder.Attributes.BindCylAttrRows import (
    BindCylAttrRows,
)
from convert.adapters.solidworks.Archive.Partition.AttachedCylinder.Attributes.CylAttrIn import (
    CylAttrIn,
)
from convert.adapters.solidworks.Archive.Partition.AttachedCylinder.Attributes.MakeCylAttrList import (
    MakeCylAttrList,
)
from convert.adapters.solidworks.Archive.Partition.AttachedCylinder.Attributes.MakeCylDefs import (
    MakeCylDefs,
)
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# every owner and the registered world link describe the same generated attribute entities
def MakeCylAttrs(
    WorldValue: XmtNode,
    BodyValue: XmtNode,
    NodesValue: tuple[XmtNode, ...],
    InputsValue: tuple[CylAttrIn, ...],
) -> tuple[tuple[XmtNode, ...], dict[int, tuple[int, ...]]]:
    NamesValue = tuple(
        dict.fromkeys(InputValue.NameValue for InputValue in InputsValue)
    )
    FirstIndex = len(NodesValue) + 2
    DefRows = MakeCylDefs(NamesValue, FirstIndex)
    RowsValue = BindCylAttrRows(
        InputsValue,
        dict(
            zip(
                NamesValue,
                (NodeValue.IndexValue for NodeValue in DefRows[::2]),
                strict=True,
            )
        ),
        FirstIndex + len(DefRows),
        BodyValue.Integer("highest_node_id"),
    )
    FirstList = FirstIndex + len(DefRows) + len(RowsValue.NodesValue)
    OwnersValue = tuple(
        (
            ReplaceValue(
                NodeValue,
                FieldsValue=dict(NodeValue.FieldsValue)
                | {
                    "attributes_features": RowsValue.OwnerHeads[NodeValue.IndexValue],
                },
            )
            if NodeValue.IndexValue in RowsValue.OwnerHeads
            else NodeValue
        )
        for NodeValue in NodesValue
    )
    OwnedBody = ReplaceValue(
        OwnersValue[0],
        FieldsValue=dict(OwnersValue[0].FieldsValue)
        | {
            "attribute_chains": FirstList,
            "highest_node_id": BodyValue.Integer("highest_node_id") + len(InputsValue),
        },
    )
    LinkedWorld = ReplaceValue(
        WorldValue,
        FieldsValue=dict(WorldValue.FieldsValue)
        | {
            "attrib_def": DefRows[-2].IndexValue,
        },
    )
    ListRows = MakeCylAttrList(
        FirstList, BodyValue.IndexValue, tuple(RowsValue.TypeHeads.values())
    )
    return (
        LinkedWorld,
        OwnedBody,
        *OwnersValue[1:],
        *DefRows,
        *RowsValue.NodesValue,
        *ListRows,
    ), RowsValue.PointerSlots
