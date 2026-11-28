from collections import Counter
from contextlib import contextmanager
from hashlib import sha256
from importlib import import_module
from struct import pack

from convert.Geometry.Parasolid import DecodePartData, EncodePartData, ParaHeaderData, ParaStream
from convert.adapters.solidworks.Archive.Partition.ImportHistory.WriteXmtEndMut import WriteXmtEndMut
from convert.adapters.solidworks.Archive.Partition.KernelShapes import KKernelShapes
from convert.adapters.solidworks.Archive.Partition.LocalWrite.GetXmtField import GetXmtField
from convert.adapters.solidworks.Archive.Partition.LocalWrite.WriteXmtNodeMut import WriteXmtNodeMut
from convert.adapters.solidworks.Archive.Partition.MakeXmtShape import MakeXmtShape
from convert.adapters.solidworks.Archive.Partition.ReadHistMarks import ReadHistMarks
from convert.adapters.solidworks.Archive.Partition.XmtCursor import XmtCursor
from convert.adapters.solidworks.Container.Format import KPartitionStream

TORUS = 54
SHAPES = KKernelShapes | {
    TORUS: MakeXmtShape(
        "TORUS",
        "node_id:d attributes_features:p1019 owner:p1007 next:p1006 previous:p1006 "
        "geometric_owner:p141 sense:c centre:v axis:v major_radius:f minor_radius:f x_axis:v",
    ),
}
NODE_READER = import_module("convert.adapters.solidworks.Archive.Partition.ReadXmtNodeMut")


def demand(condition, message):
    if not condition:
        raise ValueError(message)


@contextmanager
def saved_shapes():
    original = NODE_READER.KKernelShapes
    NODE_READER.KKernelShapes = SHAPES
    try:
        yield
    finally:
        NODE_READER.KKernelShapes = original


def active_replay(archive):
    raw_stream = archive.require(KPartitionStream)
    active, deltas = DecodePartData(raw_stream, KPartitionStream)
    header = ParaHeaderData(active.data)
    demand(header is not None and header.schema == "SCH_3701250_37102_13006"
           and header.description == ": TRANSMIT FILE (partition) created by modeller version 3701250"
           and active.wrapper_offset == 0 and deltas.wrapper_offset == active.stored_size
           and active.stored_size + deltas.stored_size == len(raw_stream),
           "saved sweep result transport differs from the measured two-frame archive")
    reader = XmtCursor(active.data[header.body_offset:])
    nodes, spans = {}, {}
    with saved_shapes():
        while (kind := reader.ReadKind()) != 1:
            start = reader.OffsetValue + header.body_offset - 2
            node = NODE_READER.ReadXmtNodeMut(reader, kind)
            demand(node.IndexValue not in nodes, "duplicate saved result record")
            nodes[node.IndexValue] = node
            spans[node.IndexValue] = (start, reader.OffsetValue + header.body_offset)
        reader.FinishRead()
        marks = ReadHistMarks(deltas.data, nodes)
    emitted, seen = bytearray(pack(">HI", 239, 0)), set()
    for node in nodes.values():
        WriteXmtNodeMut(emitted, node, SHAPES[node.KindValue], seen)
    WriteXmtEndMut(emitted)
    wire = ParaStream(bytes(emitted), header.schema, header.description.encode("ascii"))
    demand(wire == active.data and EncodePartData(wire) == raw_stream[:active.stored_size],
           "saved sweep active records did not replay both exact representations")
    torus, = of_kind(nodes, TORUS)
    return nodes, torus, {"active_sha256": sha256(wire).hexdigest(), "active_bytes": len(wire),
                         "compressed_sha256": sha256(raw_stream[:active.stored_size]).hexdigest(),
                         "active_nodes": len(nodes), "deltas_sha256": deltas.sha256,
                         "read_marks": marks, "torus_index": torus.IndexValue,
                         "torus_node_id": torus.Integer("node_id"), "torus_span": spans[torus.IndexValue]}


def of_kind(nodes, kind):
    return tuple(node for node in nodes.values() if node.KindValue == kind)


def expect(nodes, index, kind):
    node = nodes[index]
    allowed = (kind,) if type(kind) is int else kind
    demand(node.KindValue in allowed, "saved sweep link has the wrong resident class")
    return node


def follow(nodes, index, kind, next_key, previous_key=None):
    found = {}
    previous = 0
    while index:
        demand(index not in found, "cyclic saved sweep list")
        node = expect(nodes, index, kind)
        demand(previous_key is None or node.Integer(previous_key) == previous,
               "nonreciprocal saved sweep list")
        found[index] = node
        previous, index = index, node.Integer(next_key)
    return tuple(found.values())


def check_reachable(nodes, root):
    pointers = {}
    for index, node in nodes.items():
        pointers[index] = {
            pointer for slot in SHAPES[node.KindValue].FieldsValue if slot.EncodingValue == "p"
            for pointer in GetXmtField(node, slot)[1] if pointer
        }
    demand(set.union(*pointers.values()) <= nodes.keys(), "nonresident pointer in actual active result")
    seen, frontier = set(), {root.IndexValue}
    while frontier:
        seen.update(frontier)
        frontier = set.union(*(pointers[index] for index in frontier)) - seen
    demand(seen == nodes.keys(), "unreachable active result record")


def named_attributes(nodes, owner):
    result = {}
    for node in follow(nodes, owner.Integer("attributes_features"), 81, "next", "previous"):
        demand(node.Integer("owner") == owner.IndexValue, "foreign saved attribute owner")
        definition = expect(nodes, node.Integer("definition"), 80)
        label = expect(nodes, definition.Integer("identifier"), 79).String("string")
        demand(label not in result, "duplicate attribute in the measured saved result")
        fields = tuple(nodes[i].FieldsValue["values"] if i else None for i in node.Indexes("fields"))
        result[label] = fields
    return result


def check_closed_shell(nodes, world, body):
    demand(body.Integer("owner") == world.IndexValue and body.Integer("body_type") == 1
           and body.Integer("next") == body.Integer("previous") == 0, "alternate saved body ownership")
    void, solid = follow(nodes, body.Integer("region"), 19, "next", "previous")
    shell = expect(nodes, body.Integer("shell"), 13)
    front_shell = expect(nodes, void.Integer("shell"), 13)
    demand((solid.String("type"), void.String("type")) == ("S", "V")
           and solid.Integer("body") == void.Integer("body") == body.IndexValue
           and solid.Integer("shell") == shell.IndexValue and shell.Integer("body") == body.IndexValue
           and shell.Integer("region") == solid.IndexValue and front_shell.Integer("region") == void.IndexValue
           and {node.IndexValue for node in of_kind(nodes, 13)} == {shell.IndexValue, front_shell.IndexValue},
           "alternate solid or void shell")
    back = follow(nodes, shell.Integer("face"), 14, "next", "previous")
    front = follow(nodes, front_shell.Integer("front_face"), 14, "next_front", "previous_front")
    demand(len(back) == len(front) == 3 and {x.IndexValue for x in back} == {x.IndexValue for x in front}
           and {x.IndexValue for x in back} == {x.IndexValue for x in of_kind(nodes, 14)}
           and all(node.Integer("shell") == shell.IndexValue and
                   node.Integer("front_shell") == front_shell.IndexValue for node in back),
           "native faces do not bind both sides of the same solid")
    return shell, solid, back


def face_fins(nodes, faces):
    walked = {}
    for face in faces:
        loops = follow(nodes, face.Integer("loop"), 15, "next")
        fins = []
        for loop in loops:
            fin = expect(nodes, loop.Integer("halfedge"), 17)
            demand(loop.Integer("face") == face.IndexValue and fin.Integer("loop") == loop.IndexValue
                   and fin.Integer("forward") == fin.Integer("backward") == fin.IndexValue
                   and fin.Integer("vertex") == 0 and fin.Integer("curve") == 0,
                   "saved rim loop has an unrepresented ordered use")
            fins.append(fin)
        walked[face.IndexValue] = tuple(fins)
    demand({fin.IndexValue for fins in walked.values() for fin in fins}
           == {fin.IndexValue for fin in of_kind(nodes, 17)}
           and len(of_kind(nodes, 15)) == 4 and not of_kind(nodes, 18), "foreign loop or native rim vertex")
    return walked


def saved_rim_owners(nodes, torus, expected_atom, producer, producer_time):
    world, = of_kind(nodes, 101)
    body, = of_kind(nodes, 12)
    demand(world.Integer("body") == body.IndexValue, "world does not own the saved sweep body")
    check_reachable(nodes, world)
    shell, region, faces = check_closed_shell(nodes, world, body)
    fins = face_fins(nodes, faces)
    face_surfaces = {face.Integer("surface"): face for face in faces}
    surfaces = follow(nodes, body.Integer("boundary_surface"), (50, 54), "next", "previous")
    demand(len(surfaces) == 3 and set(face_surfaces) == {node.IndexValue for node in surfaces}
           and all(node.Integer("owner") == face_surfaces[node.IndexValue].IndexValue for node in surfaces),
           "saved physical carrier is detached from the owning face")
    attrs = named_attributes(nodes, body)
    demand(attrs["ATOM_ID_2001"] == (None, (expected_atom,)) and
           attrs["LAST_BODY_MODIFYING_FEATURE_ID"] == (None, (producer,)),
           "physical atom or producer is foreign to the typed sweep")
    for face in faces:
        fields = named_attributes(nodes, face)["FACE_ID_2001"]
        demand(fields[2][1:3] == (producer, producer_time), "saved face is foreign to the creating sweep")
    caps = [(surface, face_surfaces[surface.IndexValue]) for surface in surfaces if surface.KindValue == 50]
    wall = face_surfaces[torus.IndexValue]
    demand(tuple(len(fins[face.IndexValue]) for _, face in caps) == (1, 1)
           and len(fins[wall.IndexValue]) == 2, "sweep wall and cap loops do not share both rims")
    rims = []
    for plane, face in caps:
        (cap_fin,) = fins[face.IndexValue]
        wall_fin = expect(nodes, cap_fin.Integer("other"), 17)
        edge = expect(nodes, cap_fin.Integer("edge"), 16)
        curve = expect(nodes, edge.Integer("curve"), 31)
        demand(any(wall_fin is value for value in fins[wall.IndexValue])
               and wall_fin.Integer("other") == cap_fin.IndexValue
               and wall_fin.Integer("edge") == edge.IndexValue
               and {wall_fin.String("sense"), cap_fin.String("sense")} == {"+", "-"}
               and edge.Integer("halfedge") in (cap_fin.IndexValue, wall_fin.IndexValue)
               and edge.Integer("owner") == body.IndexValue and curve.Integer("owner") == edge.IndexValue,
               "rim does not own two reciprocal oppositely oriented native uses")
        rims.append((plane, face, curve, edge, cap_fin, wall_fin))
    curves = follow(nodes, body.Integer("boundary_curve"), 31, "next", "previous")
    demand(tuple(edge.IndexValue for edge in follow(nodes, body.Integer("edge"), 16, "next", "previous"))
           == tuple(edge.IndexValue for edge in of_kind(nodes, 16))
           and {rim[3].IndexValue for rim in rims} == {edge.IndexValue for edge in of_kind(nodes, 16)}
           and {rim[2].IndexValue for rim in rims} == {curve.IndexValue for curve in curves}
           == {curve.IndexValue for curve in of_kind(nodes, 31)},
           "saved edge chain differs from the two mutually owned rims")
    return rims, {"body": body.IndexValue, "region": region.IndexValue, "shell": shell.IndexValue,
                  "face_ids": [face.IndexValue for face in faces], "atom": expected_atom,
                  "face_producer": producer, "body_match": attrs["BODY_MATCH"][0][0],
                  "density": attrs["SDL/TYSA_DENSITY"][0][0], "native_result_counts": [1, 3, 2, 0],
                  "resident_classes": dict(sorted(Counter(node.KindValue for node in nodes.values()).items()))}
