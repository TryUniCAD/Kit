from convert.adapters.solidworks.Archive.Partition.LocalWrite.BindLocalAttrs import (
    KLocalAttrBlock,
)
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# the sole body indexes one head for every active type in installation order
def MakeCylAttrList(
    IndexValue: int,
    BodyIndex: int,
    HeadValues: tuple[int, ...],
) -> tuple[XmtNode, XmtNode]:
    CountValue = len(HeadValues)
    if not 0 < CountValue <= KLocalAttrBlock:
        raise ValueError("concentric attributes require the first body list block")
    return (
        XmtNode(
            IndexValue,
            70,
            {
                "node_id": 0,
                "list_type": 4,
                "notransmit": 1,
                "owner": BodyIndex,
                "next": 0,
                "previous": 0,
                "list_length": CountValue,
                "block_length": KLocalAttrBlock,
                "finger_index": 1,
                "finger_block": IndexValue + 1,
                "list_block": IndexValue + 1,
            },
        ),
        XmtNode(
            IndexValue + 1,
            74,
            {
                "n_entries": CountValue,
                "index_map_offset": 0,
                "next_block": 0,
                "entries": (*HeadValues, *((0,) * (KLocalAttrBlock - CountValue))),
            },
        ),
    )
