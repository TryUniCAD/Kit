from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode

# ghost pointer lists use the format fixed native pointer capacity
KGhostListCapacity = 20

# a native integer ghost identity must resolve this exact typed attribute definition
KGhostBodyKey = "GHOST_REF_BODY_ID_2001"


# body and edge definitions describe legal kernel owner kinds with an explicit integer attribute value
def MakeGhostDefs(FirstIndex: int) -> tuple[XmtNode, XmtNode, XmtNode, XmtNode]:
    BodyIndex, EdgeIndex, BodyName, EdgeName = range(FirstIndex, FirstIndex + 4)
    return (
        MakeGhostDef(BodyIndex, EdgeIndex, BodyName, 2),
        MakeGhostDef(EdgeIndex, 0, EdgeName, 6),
        XmtNode(BodyName, 79, {"string": KGhostBodyKey}),
        XmtNode(EdgeName, 79, {"string": "EDGE_ID_2001"}),
    )


# attribution is a native pair of string selector and integer payload under one typed definition
def MakeGhostDef(
    IndexValue: int, NextValue: int, TextValue: int, OwnerKind: int
) -> XmtNode:
    return XmtNode(
        IndexValue,
        80,
        {
            "next": NextValue,
            "identifier": TextValue,
            "type_id": 9000,
            "actions": (0, 0, 0, 0, 3, 6, 0, 0),
            "field_names": 0,
            "legal_owners": tuple(
                int(SlotValue == OwnerKind) for SlotValue in range(17)
            ),
            "fields": (9, 1),
        },
    )


# a ghost body or edge attribute retains its actual owner and typed data reference
def MakeGhostLink(
    IndexValue: int, NodeId: int, SchemaValue: int, OwnerValue: int, ValueIndex: int
) -> XmtNode:
    return XmtNode(
        IndexValue,
        81,
        {
            "node_id": NodeId,
            "definition": SchemaValue,
            "owner": OwnerValue,
            "next": 0,
            "previous": 0,
            "next_of_type": 0,
            "previous_of_type": 0,
            "fields": (0, ValueIndex),
        },
    )


# attached body and edge attributes are indexed after the actual local shape residents
def MakeGhostAttr(
    FirstIndex: int,
    BodyValue: int,
    EdgeValue: int,
    LastEntity: int,
    BodySchema: int,
    EdgeSchema: int,
    GhostId: int,
) -> tuple[XmtNode, XmtNode, XmtNode, XmtNode, XmtNode]:
    if BodyValue == EdgeValue or not 0 < GhostId < 0x7FFFFFFF:
        raise ValueError("ghost attributes require actual distinct cell owners")
    BodyLink, BodyData, EdgeLink, ChainValue, BlockValue = range(
        FirstIndex, FirstIndex + 5
    )
    EntryValues = (EdgeLink, BodyLink)
    return (
        MakeGhostLink(BodyLink, LastEntity + 2, BodySchema, BodyValue, BodyData),
        XmtNode(BodyData, 82, {"values": (GhostId,)}),
        MakeGhostLink(EdgeLink, LastEntity + 1, EdgeSchema, EdgeValue, 0),
        XmtNode(
            ChainValue,
            70,
            {
                "node_id": 0,
                "list_type": 4,
                "notransmit": 1,
                "owner": BodyValue,
                "next": 0,
                "previous": 0,
                "list_length": len(EntryValues),
                "block_length": KGhostListCapacity,
                "finger_index": len(EntryValues) - 1,
                "finger_block": BlockValue,
                "list_block": BlockValue,
            },
        ),
        XmtNode(
            BlockValue,
            74,
            {
                "n_entries": len(EntryValues),
                "index_map_offset": 0,
                "next_block": 0,
                "entries": EntryValues + (0,) * (KGhostListCapacity - len(EntryValues)),
            },
        ),
    )
