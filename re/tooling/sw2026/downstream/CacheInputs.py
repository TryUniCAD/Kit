from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from operator import attrgetter

from para.DownstreamIds import DownstreamIds, allocate_fresh_downstream, owned_solid_chains, owner_key
from para.Tracking import FILETIME_TICKS_PER_SECOND, filetime_ticks, unsigned
from para.concentric.CylinderFace import words
from para.rectangle.Allocate import Ref


ARCHIVE_VERSION = 19000
BUILD_DATE_CODE = 2026306


@dataclass(frozen=True)
class EdgeIncidence:
    edge: Ref
    downstream_id: int
    faces: tuple[Ref, Ref]
    face_ids: tuple[int, int]
    face_role_ids: tuple[tuple[int, int], tuple[int, int]]
    positive_fin: Ref


@dataclass(frozen=True)
class PartCacheInputs:
    allocation: DownstreamIds
    incidence: tuple[EdgeIncidence, ...]


def initial_prefix(offset_minutes):
    if type(offset_minutes) is not int:
        raise TypeError("the target calendar offset must be an integer number of minutes")
    local = timezone(timedelta(minutes=offset_minutes))
    sentinel = datetime(1990, 1, 1, tzinfo=local)
    delta = sentinel - datetime(1970, 1, 1, tzinfo=timezone.utc)
    return {
        "f08": 1, "f0c": ARCHIVE_VERSION, "f10": BUILD_DATE_CODE, "f14": 0, "f18": 0,
        "f1c": 101, "f20": 101, "f28": delta.days * 86400 + delta.seconds,
    }


def finalized_part_prefix(part, next_id):
    header = part.HeaderValue
    if (part.SystemValue.RootValue.ClassValue.NameValue != "moPart_c"
            or header.ClassValue.NameValue != "moHeader_c" or header.FieldsValue["fec"] != 1):
        raise ValueError("populated part cache requires the actual configuration model header")
    if unsigned(next_id, 32, "next downstream ID") == 0:
        raise ValueError("the next downstream ID cannot use the reserved null ID")
    fields = header.FieldsValue
    return {
        "f08": next_id, "f0c": ARCHIVE_VERSION, "f10": BUILD_DATE_CODE,
        "f14": ARCHIVE_VERSION, "f18": BUILD_DATE_CODE,
        "f1c": unsigned(fields["f40"], 32, "model update counter"),
        "f20": unsigned(fields["f44"], 32, "model body counter"),
        "f28": unsigned(fields["f48"], 32, "model header update time"),
    }


def attached_part_chains(partition, allocation, updated_at):
    faces, edges = owned_solid_chains(partition.nodes, identity=attrgetter("index"))
    nodes = {node.index: node for node in partition.nodes}
    last_id = len(faces) + len(edges)
    second = filetime_ticks(updated_at, 0)
    if (allocation.is_assembly is not False or allocation.key != owner_key(allocation.owner)
            or not second <= allocation.updated < second + FILETIME_TICKS_PER_SECOND
            or len(allocation.faces) != len(faces) or len(allocation.edges) != len(edges)
            or tuple(value for _, value in allocation.faces + allocation.edges) != tuple(range(1, last_id + 1))
            or allocation.next_id != last_id + 1):
        raise ValueError("downstream cache needs the actual fresh part allocation and update time")
    for entity, operation in zip(faces + edges, allocation.installations(), strict=True):
        if words(nodes, entity, operation.definition, 0) != operation.fields[0]:
            raise ValueError("downstream allocation differs from the attached partition")
    return nodes, faces, edges


def topology_node(nodes, reference, kind):
    node = nodes.get(reference)
    if node is None or node.kind != kind:
        raise ValueError("downstream incidence reaches an invalid topology kind")
    return node


def loop_fins(nodes, loop, face, fin_faces, *, identity=attrgetter("ref")):
    start = loop.fields["halfedge"]
    if start in fin_faces:
        raise ValueError("downstream incidence repeats a loop fin")
    current = start
    while current not in fin_faces:
        fin = topology_node(nodes, current, 17)
        following = topology_node(nodes, fin.fields["forward"], 17)
        if fin.fields["loop"] != identity(loop) or following.fields["backward"] != current:
            raise ValueError("downstream fin ring has an invalid owner or backlink")
        fin_faces[current] = face
        current = identity(following)
    if current != start:
        raise ValueError("downstream incidence enters a foreign fin ring")


def face_incidence(nodes, faces, *, identity=attrgetter("ref")):
    fin_faces = {}
    loops = set()
    for face in faces:
        current = face.fields["loop"]
        while current:
            loop = topology_node(nodes, current, 15)
            if current in loops or loop.fields["face"] != identity(face):
                raise ValueError("downstream face loop has an invalid or repeated owner")
            loops.add(current)
            loop_fins(nodes, loop, identity(face), fin_faces, identity=identity)
            current = loop.fields["next"]
    return fin_faces


def prepare_part_cache_inputs(topology, owner, updated_at, subsecond_ticks):
    faces, edges = owned_solid_chains(topology)
    allocation = allocate_fresh_downstream(faces, edges, owner, updated_at, subsecond_ticks, is_assembly=False)
    nodes = {node.ref: node for node in topology}
    fin_faces = face_incidence(nodes, faces)
    face_ids = dict(allocation.faces)
    occurrences = set()
    rows = []
    for edge, (edge_ref, edge_id) in zip(edges, allocation.edges, strict=True):
        first = topology_node(nodes, edge.fields["halfedge"], 17)
        second = topology_node(nodes, first.fields["other"], 17)
        if (first.ref == second.ref or second.fields["other"] != first.ref
                or first.fields["edge"] != edge_ref or second.fields["edge"] != edge_ref
                or first.ref not in fin_faces or second.ref not in fin_faces):
            raise ValueError("downstream edge requires two linked fin owners")
        first_face = fin_faces[first.ref]
        second_face = fin_faces[second.ref]
        curve = nodes.get(edge.fields.get("curve"))
        if curve is None or curve.kind not in (30, 31) or curve.fields.get("owner") != edge_ref:
            raise ValueError("downstream face roles require a line or circle curve owner")
        sense = first.fields["sense"], second.fields["sense"]
        if set(sense) != {"+", "-"}:
            raise ValueError("downstream face roles require opposite fin senses")
        ids = face_ids[first_face], face_ids[second_face]
        left, right = ids if sense[0] == "+" else ids[::-1]
        positive_fin = first.ref if sense[0] == "+" else second.ref
        rows.append(EdgeIncidence(
            edge_ref, edge_id, (first_face, second_face), ids, ((0, left), (1, right)), positive_fin,
        ))
        occurrences.update((first.ref, second.ref))
    if occurrences != fin_faces.keys() or occurrences != {node.ref for node in topology if node.kind == 17}:
        raise ValueError("downstream edge and face incidence covers different fins")
    return PartCacheInputs(allocation, tuple(rows))
