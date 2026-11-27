from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Partition.LocalWrite.LocalAttrDefs import (
    LocalAttrDefs,
)
from convert.adapters.solidworks.Archive.Partition.LocalWrite.LocalAttrRows import (
    LocalAttrRows,
)
from convert.adapters.solidworks.Archive.Partition.LocalWrite.LocalBodyOwner import (
    LocalBodyOwner,
)
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode

# the native pointer list layout owns twenty resident member slots in its first block
KLocalAttrBlock = 20


# the body receives computed attribute and type index links without mutating the input
def BindLocalAttrs(
    NodesValue: tuple[XmtNode, ...],
    OwnerValue: LocalBodyOwner,
) -> tuple[XmtNode, ...]:
    BodyValue, *Boundary = NodesValue
    DefinitionIndex = len(NodesValue) + 1
    Definitions = LocalAttrDefs(DefinitionIndex)
    RowsValue, Entries = LocalAttrRows(
        BodyValue, OwnerValue, DefinitionIndex, DefinitionIndex + len(Definitions)
    )
    ListIndex = RowsValue[-1].IndexValue + 1
    BlockIndex = ListIndex + 1
    CountValue = len(Entries)
    ListValue = XmtNode(
        ListIndex,
        70,
        {
            "node_id": 0,
            "list_type": 4,
            "notransmit": 1,
            "owner": BodyValue.IndexValue,
            "next": 0,
            "previous": 0,
            "list_length": CountValue,
            "block_length": KLocalAttrBlock,
            "finger_index": 1,
            "finger_block": BlockIndex,
            "list_block": BlockIndex,
        },
    )
    BlockValue = XmtNode(
        BlockIndex,
        74,
        {
            "n_entries": CountValue,
            "index_map_offset": 0,
            "next_block": 0,
            "entries": (*Entries, *((0,) * (KLocalAttrBlock - CountValue))),
        },
    )
    Replacement = ReplaceValue(
        BodyValue,
        FieldsValue=dict(BodyValue.FieldsValue)
        | {
            "attribute_chains": ListIndex,
            "attributes_features": Entries[-1],
            "highest_node_id": RowsValue[-1].Integer("node_id"),
        },
    )
    return Replacement, *Boundary, *Definitions, *RowsValue, ListValue, BlockValue
