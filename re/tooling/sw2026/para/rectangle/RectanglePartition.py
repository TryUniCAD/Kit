from dataclasses import dataclass, replace

from .Allocate import IncompletePartition, Ref, index_draft, require
from .Geometry import chain
from .RectangleAttributes import append_rectangle_attributes
from builders.EmptyPartition import WORLD_KIND
from convert.Geometry.Parasolid import KMissingParam
from para.Partition import History, Node, Partition, Rollback, validate
from para.Schema import SCHEMAS


SESSION_LINEAR_SCALE = 1e-8
SESSION_PRECISION = 1e-11
BODY_STABLE_STATE = 1
BODY_SOLID_KIND = 1
NOMINAL_GEOMETRY_STATE = 1
FIRST_BODY_ENTITY_ID = 1


WORLD_AUXILIARY = (
    "assembly", "attribute", "transform", "surface", "curve", "point", "mesh", "polyline", "lattice",
    "attdef_list", "index_map_offset", "index_map", "schema_embedding_map", "mesh_offset_data",
)
BODY_AUXILIARY = (
    "lattice", "surface", "curve", "point", "mesh", "polyline", "key", "ref_instance", "next", "previous",
    "boundary_lattice", "boundary_mesh", "boundary_polyline", "child", "index_map_offset", "index_map",
    "node_id_index_map", "schema_embedding_map", "mesh_offset_data",
)
NODE_IDS = (13, 14, 15, 16, 18, 19, 29, 30, 50)
NO_ATTRIBUTES = (13, 14, 15, 16, 17, 18, 19, 29, 30, 50)
LOCAL_TOLERANCE = (14, 16, 18)
BODY_CHAIN_KINDS = (16, 18, 29, 30, 50)


@dataclass(frozen=True)
class ProjectedRectangle:
    partition: Partition
    transient_pointer_allocations: tuple[Ref, ...]

    def require_archive_attachment(self):
        raise IncompletePartition("populated archive attachment needs verified f1010, live-body map mode and boss f540")


def absent(*names):
    return dict.fromkeys(names, 0)


def augment(node, **values):
    require(not (node.fields.keys() & values.keys()), f"duplicate topology field on {node.ref.name}")
    return replace(node, fields={**node.fields, **values})


def vertex_fins(nodes):
    fins = {node.ref: node.fields for node in nodes if node.kind == 17}
    vertices = {}
    for ref, fields in fins.items():
        vertices.setdefault(fields["vertex"], []).append(ref)
    heads, links = {}, {}
    for vertex, incident in vertices.items():
        first, *_ = incident
        remaining = set(incident)
        heads[vertex] = first
        current = first
        require(len(remaining) == 3, "a rectangular solid vertex needs three fins")
        while remaining:
            require(current in remaining, "vertex rotation does not cover its fins")
            remaining.remove(current)
            following = fins[fins[current]["forward"]]["other"]
            require(fins[following]["vertex"] == vertex, "rotation crosses a vertex")
            links[current] = following if remaining else 0
            current = following
        require(current == first, "vertex rotation does not close")
    return heads, links


def complete_topology(plan):
    nodes = plan.topology
    next_id = FIRST_BODY_ENTITY_ID
    heads, radial = vertex_fins(nodes)
    groups = {kind: chain(node.ref.name for node in nodes if node.kind == kind) for kind in BODY_CHAIN_KINDS}
    complete = []
    for node in nodes:
        fields = {}
        kind = node.kind
        if kind == WORLD_KIND:
            fields.update(absent(*WORLD_AUXILIARY))
        elif kind == 12:
            fields.update(absent(*BODY_AUXILIARY), res_size=SESSION_LINEAR_SCALE / SESSION_PRECISION,
                          res_linear=SESSION_LINEAR_SCALE, state=BODY_STABLE_STATE, body_type=BODY_SOLID_KIND,
                          nom_geom_state=NOMINAL_GEOMETRY_STATE, lowest_node_id=0)
        if kind in NODE_IDS:
            fields["node_id"] = next_id
            next_id += 1
        if kind in NO_ATTRIBUTES:
            fields["attributes_features"] = 0
        if kind in LOCAL_TOLERANCE:
            fields["tolerance"] = KMissingParam
        if kind in BODY_CHAIN_KINDS:
            fields["previous"], fields["next"] = groups[kind][node.ref.name]
        if kind in (30, 50):
            fields["geometric_owner"] = 0
        if kind == 13:
            fields.update(absent("next", "edge", "vertex"))
        elif kind == 17:
            fields["next_at_vx"] = radial[node.ref]
        elif kind == 18:
            fields["halfedge"] = heads[node.ref]
        elif kind == 19:
            fields.update(absent("frame", "owner"))
        complete.append(augment(node, **fields))
    return tuple(complete), next_id


def collect_state(draft, pointer_allocations):
    selected, initial, activation = draft.marks
    geometry_world, activation_world = draft.previous_worlds
    local_kinds = {node.index for node in draft.active if node.kind not in (79, 80, WORLD_KIND)}
    journal = tuple(reversed(draft.geometry_rollback_members))
    require({index for index, _ in journal} == local_kinds, "rollback needs every new transmitted body node once")
    require(len(pointer_allocations) == len(set(pointer_allocations)), "a runtime pointer array cannot be allocated twice")
    history = (
        History(add_counts(selected, len(journal) + len(pointer_allocations)), Rollback(journal, previous(geometry_world))),
        History(add_counts(initial), None),
        History(add_counts(activation), Rollback((), previous(activation_world))),
    )
    partition = Partition(draft.active, draft.partition, history)
    validate(partition)
    return partition


def previous(node):
    return Node(node.index, WORLD_KIND, {**absent(*WORLD_AUXILIARY, "attrib_def"), **node.fields})


def add_counts(mark, new=0):
    return Node(mark.index, mark.kind, {**mark.fields, "n_new_nodes": new, "n_del_nodes": 0, "n_copy_mod_nodes": 0})


def project_rectangle(child, plan, appearance, previous_face_allocations=0):
    partial, next_id = complete_topology(plan)
    active, nontransmitted, next_id = append_rectangle_attributes(
        child, plan, partial, appearance, next_id, previous_face_allocations,
    )
    complete = tuple(augment(node, highest_node_id=next_id - 1) if node.kind == 12 else node for node in active)
    for node in complete:
        expected = {field.name for field in SCHEMAS[node.kind].current}
        require(node.fields.keys() == expected,
                f"unclassified {SCHEMAS[node.kind].name} fields {sorted(expected ^ node.fields.keys())}")
    draft = index_draft(complete, plan.history)
    return ProjectedRectangle(collect_state(draft, nontransmitted), nontransmitted)
