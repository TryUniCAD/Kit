from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from SweepGhostGraph import BODY_KEY, EDGE_KEY
from SweepModel import require


DEFINITION_ACTIONS = (0, 0, 0, 0, 3, 6, 0, 0)
DEFINITION_FIELD_KINDS = (9, 1)
DEFINITION_OWNER_COUNT = 17
POINTER_BLOCK_LENGTH = 20


def definition(index, following, identifier, owner_kind):
    return XmtNode(index, 80, {"next": following, "identifier": identifier, "type_id": 9000,
                              "actions": DEFINITION_ACTIONS, "field_names": 0,
                              "legal_owners": tuple(int(slot == owner_kind) for slot in range(DEFINITION_OWNER_COUNT)),
                              "fields": DEFINITION_FIELD_KINDS})


def definitions(first):
    body_def, edge_def, body_name, edge_name = range(first, first + 4)
    return (definition(body_def, edge_def, body_name, 2), definition(edge_def, 0, edge_name, 6),
            XmtNode(body_name, 79, {"string": BODY_KEY}), XmtNode(edge_name, 79, {"string": EDGE_KEY}))


def attribute(index, node_id, schema, owner, value_index):
    return XmtNode(index, 81, {"node_id": node_id, "definition": schema, "owner": owner,
                              "next": 0, "previous": 0, "next_of_type": 0, "previous_of_type": 0,
                              "fields": (0, value_index)})


def body_attributes(first, body, edge, last_entity, body_def, edge_def, ghost_id):
    require(body != edge and 0 < ghost_id < 0x7fffffff, "ghost attributes require actual distinct cell owners")
    body_attr, body_value, edge_attr, chain, block = range(first, first + 5)
    entries = (edge_attr, body_attr)
    return (
        attribute(body_attr, last_entity + 2, body_def, body, body_value),
        XmtNode(body_value, 82, {"values": (ghost_id,)}),
        attribute(edge_attr, last_entity + 1, edge_def, edge, 0),
        XmtNode(chain, 70, {"node_id": 0, "list_type": 4, "notransmit": 1, "owner": body, "next": 0, "previous": 0,
                           "list_length": len(entries), "block_length": POINTER_BLOCK_LENGTH, "finger_index": len(entries) - 1,
                           "finger_block": block, "list_block": block}),
        XmtNode(block, 74, {"n_entries": len(entries), "index_map_offset": 0, "next_block": 0,
                           "entries": entries + (0,) * (POINTER_BLOCK_LENGTH - len(entries))}),
    )
