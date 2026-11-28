from dataclasses import dataclass, replace
from math import isfinite

from .Allocate import DraftNode, Ref, positive_i32, require
from .Attributes import Field, Owner, RECTANGLE_DEFINITION_BY_NAME, build_definitions


BLOCK_CAPACITY = 20
OWNER_CLASS = {12: Owner.BODY, 14: Owner.FACE, 16: Owner.EDGE}
SCALAR_FIELDS = {
    Field.INT: (82, lambda v: type(v) is int and -(1 << 31) <= v < 1 << 31),
    Field.REAL: (83, lambda v: type(v) in (int, float) and isfinite(v)),
    Field.UNICODE: (98, lambda v: type(v) is int and 0 <= v < 1 << 16),
}


@dataclass(frozen=True)
class Install:
    owner: Ref
    definition: str
    fields: tuple[tuple | None, ...]

    @property
    def reference(self):
        return Ref(f"{self.owner.name}:attribute:{self.definition}")


@dataclass(frozen=True)
class AttributeGraph:
    owners: tuple[DraftNode, ...]
    chains: tuple[DraftNode, ...]
    next_identifier: int


def value_nodes(installation, definition):
    require(len(installation.fields) == len(definition.fields),
            f"attribute slot count differs for {definition.name}")
    refs, nodes = [], []
    for slot, (field, value) in enumerate(zip(definition.fields, installation.fields, strict=True)):
        if value is None:
            refs.append(0)
            continue
        require(field in SCALAR_FIELDS, f"cannot transmit {definition.name} field {slot} kind {field.name}")
        kind, admissible = SCALAR_FIELDS[field]
        require(isinstance(value, tuple) and value and all(map(admissible, value)),
                f"invalid scalar array for {definition.name} field {slot}")
        ref = Ref(f"{installation.reference.name}:field:{slot}")
        refs.append(ref)
        nodes.append(DraftNode(ref, kind, {"values": value}))
    return tuple(refs), tuple(nodes)


def attach_attributes(owners, body, installations, first_identifier):
    by_ref = {node.ref: node for node in owners}
    require(len(by_ref) == len(owners) and by_ref[body].kind == 12, "attribute scope requires a unique body")
    owner_heads, type_heads, attrs = {}, {}, {}
    nodes = []
    identifier = positive_i32(first_identifier, "first attributed entity identifier")
    for operation in installations:
        owner = by_ref[operation.owner]
        definition = RECTANGLE_DEFINITION_BY_NAME[operation.definition]
        require(OWNER_CLASS[owner.kind] in definition.owners and operation.reference not in attrs,
                f"attribute {definition.name} requires a unique, legal owner")
        previous_owner_head = owner_heads.get(operation.owner, 0)
        previous_type_head = type_heads.get(definition.name, 0)
        if previous_owner_head:
            attrs[previous_owner_head]["previous"] = operation.reference
        if previous_type_head:
            attrs[previous_type_head]["previous_of_type"] = operation.reference
        owner_heads[operation.owner] = operation.reference
        type_heads[definition.name] = operation.reference
        values, additional = value_nodes(operation, definition)
        attrs[operation.reference] = {
            "node_id": identifier,
            "definition": definition.reference,
            "owner": owner.ref,
            "next": previous_owner_head,
            "previous": 0,
            "next_of_type": previous_type_head,
            "previous_of_type": 0,
            "fields": values,
        }
        nodes.append(DraftNode(operation.reference, 81, attrs[operation.reference]))
        nodes.extend(additional)
        identifier = positive_i32(identifier + 1, "next attributed entity identifier")
    count = len(type_heads)
    require(0 < count <= BLOCK_CAPACITY, "only the first body attribute list block is admitted")
    list_ref = Ref(body.name + ":attribute-chains")
    block_ref = Ref(body.name + ":attribute-chain-block")
    nodes.extend((
        DraftNode(list_ref, 70, {
            "node_id": 0, "list_type": 4, "notransmit": 1, "owner": body, "next": 0, "previous": 0,
            "list_length": count, "block_length": BLOCK_CAPACITY, "finger_index": 1,
            "finger_block": block_ref, "list_block": block_ref,
        }),
        DraftNode(block_ref, 74, {
            "n_entries": count, "index_map_offset": 0, "next_block": 0,
            "entries": (*type_heads.values(), *((0,) * (BLOCK_CAPACITY - count))),
        }),
    ))
    for ref, head in owner_heads.items():
        node = by_ref[ref]
        require(not node.fields.get("attributes_features"), "cannot replace a populated attribute link")
        by_ref[ref] = replace(node, fields={**node.fields, "attributes_features": head})
    body_node = by_ref[body]
    require(not body_node.fields.get("attribute_chains"), "cannot replace a populated body attribute chain")
    by_ref[body] = replace(body_node, fields={**body_node.fields, "attribute_chains": list_ref})
    return AttributeGraph(tuple(by_ref.values()), tuple(nodes), identifier)


def register_attributes(topology, body, installations, first_identifier):
    graph = attach_attributes(topology, body, installations, first_identifier)
    names = tuple(dict.fromkeys(installation.definition for installation in installations))
    definition_head, declarations = build_definitions(tuple(reversed(names)))
    world, *owners = graph.owners
    require(world.ref == Ref("world"), "attribute declarations belong to the active world")
    active = (
        replace(world, fields={**world.fields, "attrib_def": definition_head}),
        *owners,
        *declarations,
        *graph.chains,
    )
    pointer_allocations = tuple(
        Ref(f"{op.reference.name}:pointer-field:{index}")
        for op in installations
        for index, field in enumerate(RECTANGLE_DEFINITION_BY_NAME[op.definition].fields)
        if field is Field.POINTER
    )
    return active, pointer_allocations, graph.next_identifier
