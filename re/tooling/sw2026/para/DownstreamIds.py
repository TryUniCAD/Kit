from dataclasses import dataclass
from struct import iter_unpack
from uuid import UUID

from builders.EmptyPartition import WORLD_KIND
from para.Tracking import filetime_ticks, signed_dword, unsigned
from para.rectangle.Allocate import DraftNode, Ref
from para.rectangle.AttributeChains import Install


HASH_MODULUS = 1_000_000_009
WORD_MASK = 0xffffffff
FACE_DEFINITION = "DOWNSTREAM_FACE_ID"
EDGE_DEFINITION = "DOWNSTREAM_EDGE_ID"


def polynomial(units, base):
    power = 1
    value = 0
    for unit in units:
        value = (value + unit * power) % HASH_MODULUS
        power = (power * base) % HASH_MODULUS
    return value


def owner_key(owner: UUID) -> int:
    if type(owner) is not UUID:
        raise ValueError("downstream model owner must be its actual UUID")
    units = tuple(unit for (unit,) in iter_unpack("<H", str(owner).encode("utf-16-le")))
    return (polynomial(units, 32771) << 32) | polynomial(units, 32779)


def order_ids(members, first):
    return tuple((member.ref, ordinal) for ordinal, member in enumerate(members, first))


@dataclass(frozen=True)
class DownstreamIds:
    owner: UUID
    key: int
    updated: int
    is_assembly: bool
    faces: tuple[tuple[Ref, int], ...]
    edges: tuple[tuple[Ref, int], ...]
    next_id: int

    @property
    def archive_owner_fields(self) -> tuple[str, int, int]:
        return str(self.owner), self.key >> 32, self.key & WORD_MASK

    def installations(self) -> tuple[Install, ...]:
        return tuple(
            Install(reference, definition, ((
                signed_dword(identifier),
                signed_dword(self.updated & WORD_MASK),
                signed_dword(self.updated >> 32),
                int(self.is_assembly),
                signed_dword(self.key & WORD_MASK),
                signed_dword(self.key >> 32),
            ), None, None))
            for definition, members in ((FACE_DEFINITION, self.faces), (EDGE_DEFINITION, self.edges))
            for reference, identifier in members
        )


def allocate_fresh_downstream(
    faces: tuple[DraftNode, ...],
    edges: tuple[DraftNode, ...],
    owner: UUID,
    updated_at: int,
    subsecond_ticks: int,
    *,
    is_assembly: bool,
) -> DownstreamIds:
    if type(is_assembly) is not bool:
        raise ValueError("downstream context must be the actual assembly flag")
    for members, kind in ((faces, 14), (edges, 16)):
        if not members or any(type(member) is not DraftNode or member.kind != kind for member in members):
            raise ValueError("downstream allocation requires ordered actual face and edge owners")
    references = tuple(member.ref for member in (*faces, *edges))
    if not all(type(reference) is Ref and reference.name for reference in references) or len(set(references)) != len(references):
        raise ValueError("downstream owners must have distinct topology identities")
    first_edge = len(faces) + 1
    next_id = unsigned(first_edge + len(edges), 32, "next downstream identifier")
    return DownstreamIds(
        owner, owner_key(owner), filetime_ticks(updated_at, subsecond_ticks), is_assembly,
        order_ids(faces, 1), order_ids(edges, first_edge), next_id,
    )


def owned_solid_chains(
    topology: tuple[DraftNode, ...],
) -> tuple[tuple[DraftNode, ...], tuple[DraftNode, ...]]:
    nodes = {node.ref: node for node in topology}
    bodies = tuple(node for node in topology if node.kind == 12)
    if len(nodes) != len(topology) or len(bodies) != 1:
        raise ValueError("downstream chain projection requires one uniquely owned solid")
    body, = bodies
    world = nodes.get(body.fields.get("owner"))
    if (world is None or world.kind != WORLD_KIND or world.fields.get("body") != body.ref
            or body.fields.get("body_type") != 1 or body.fields.get("ref_instance") or body.fields.get("child")):
        raise ValueError("downstream chain projection requires an ordinary world-owned solid body")

    def walk(start, kind, owner_field, owner, *, has_previous=False):
        found = {}
        current = start
        previous = 0
        while current:
            node = nodes.get(current)
            if (node is None or node.kind != kind or current in found or
                    node.fields.get(owner_field) != owner or
                    (has_previous and node.fields.get("previous") != previous)):
                raise ValueError("downstream topology chain has an invalid or foreign member")
            found[current] = node
            previous, current = current, node.fields["next"]
        return tuple(found.values())

    regions = walk(body.fields["region"], 19, "body", body.ref, has_previous=True)
    if any(region.fields.get("frame") for region in regions):
        raise ValueError("downstream chain projection requires unframed solid regions")
    shells = tuple(
        shell for region in regions for shell in walk(region.fields["shell"], 13, "region", region.ref)
    )
    faces = tuple(
        face for shell in shells for face in walk(shell.fields["face"], 14, "shell", shell.ref, has_previous=True)
    )
    edges = (*walk(body.fields["edge"], 16, "owner", body.ref, has_previous=True), *(
        edge for shell in shells for edge in walk(shell.fields["edge"], 16, "owner", shell.ref, has_previous=True)
    ))
    for kind, ordered in ((19, regions), (13, shells), (14, faces), (16, edges)):
        references = {node.ref for node in ordered}
        if len(references) != len(ordered) or references != {node.ref for node in topology if node.kind == kind}:
            raise ValueError("downstream topology chain omits or repeats a member")
    return faces, edges


def install_part_downstream(
    topology: tuple[DraftNode, ...],
    existing: tuple[Install, ...],
    allocation: DownstreamIds,
) -> tuple[Install, ...]:
    faces, edges = owned_solid_chains(topology)
    first_edge = len(faces) + 1
    if (allocation.is_assembly is not False or allocation.faces != order_ids(faces, 1)
            or allocation.edges != order_ids(edges, first_edge) or allocation.next_id != first_edge + len(edges)
            or allocation.key != owner_key(allocation.owner)):
        raise ValueError("downstream identities must follow the actual linked part topology and owner")
    unsigned(allocation.updated, 64, "downstream update FILETIME")
    additions = {(operation.definition, operation.owner): operation for operation in allocation.installations()}
    operations = []
    for operation in existing:
        if operation.definition in (FACE_DEFINITION, EDGE_DEFINITION):
            key = (operation.definition, operation.owner)
            if key not in additions:
                raise ValueError("existing downstream record has a foreign or repeated owner")
            operation = additions.pop(key)
        operations.append(operation)
    return (*operations, *additions.values())
