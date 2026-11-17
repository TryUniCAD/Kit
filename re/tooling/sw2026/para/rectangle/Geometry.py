from dataclasses import dataclass
from itertools import product
from math import isclose

from .Allocate import DraftNode, Ref, allocate_marks, allocate_tracking, allocate_updates, require, world
from convert.Geometry.Extrude.Polygon.PolygonExtrude import BuildPrism
import interchange.brep.Validation.BrepValidate
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.geometry.Models.VectorSpace import SpaceVector


MM_PER_M = 1000


@dataclass(frozen=True)
class FaceRole:
    cap: bool
    number: int


@dataclass(frozen=True)
class RectanglePlan:
    brep: object
    bounds_mm: tuple
    volume_mm3: float
    area_mm2: float
    face_roles: dict
    history: object
    tracking: object
    archive: object
    topology: tuple[DraftNode, ...]


def vector(value):
    return (value.x, value.y, value.z)


def metres(value):
    return tuple(component / MM_PER_M for component in vector(value))


def point(node):
    position = node["pos"]
    return PlaneVector(position["x"] * MM_PER_M, position["y"] * MM_PER_M)


def rectangle(child):
    model, extrusion, profile = child.model, child.extrusion, child.profile
    require(model.cls == "moPart_c" and extrusion is not None and extrusion.feature.cls == "moExtrusion_c"
            and extrusion.profile is profile and extrusion.condition == "blind" and not extrusion.reverse_direction
            and profile.arc_count == 0 and profile.line_count == 4 and not child.revolution and not child.blind_pocket,
            "cache construction requires one forward blind rectangular boss")
    frame = profile.profile["_frame"]
    require((tuple(frame.origin), tuple(frame.u), tuple(frame.v), tuple(frame.normal)) ==
            ((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)), "rectangle draft requires the standard Front plane")
    lines = tuple(profile.sketch["_line_nodes"])
    edges = tuple(LineGeometry(point(line["_start"]), point(line["_end"])) for line in lines)
    starts = tuple((edge.start.x, edge.start.y) for edge in edges)
    finishes = tuple((edge.end.x, edge.end.y) for edge in edges)
    xs, ys = (sorted(set(axis)) for axis in zip(*starts, strict=True))
    require(len(xs) == len(ys) == 2 and set(starts) == set(product(xs, ys))
            and finishes == starts[1:] + starts[:1], "profile does not contain the four connected rectangle sides")
    profile_edges = {}
    for line, start, finish in zip(lines, starts, finishes, strict=True):
        constant, = [i for i, (a, b) in enumerate(zip(start, finish, strict=True)) if a == b]
        profile_edges[(constant, start[constant])] = line["f08"]
    require(len(profile_edges) == len(set(profile_edges.values())) == 4, "rectangle sides need unique sketch line ids")
    transform = Transform(SpaceVector(*frame.origin), SpaceVector(*frame.u), SpaceVector(*frame.v), SpaceVector(*frame.normal))
    depth = extrusion.depth * MM_PER_M
    geometry, volume, area, bounds = BuildPrism(
        "rectangle-" + str(extrusion.feature["f08"]), transform, edges, 0.0, depth,
    )
    surfaces = {surface.id: surface for surface in geometry.surfaces}
    roles = {}
    for face in geometry.faces:
        surface = surfaces[face.surface_id]
        along_z = abs(surface.normal.z) == 1.0
        if along_z:
            roles[face.id] = FaceRole(True, int(isclose(surface.origin.z, depth)))
        else:
            axis = 0 if abs(surface.normal.x) == 1.0 else 1
            roles[face.id] = FaceRole(False, profile_edges[(axis, vector(surface.origin)[axis])])
    return geometry, (vector(bounds.minimum), vector(bounds.maximum)), volume, area, roles


def chain(identifiers):
    names = tuple(identifiers)
    return {name: (Ref(names[index - 1]) if index else 0,
                   Ref(names[index + 1]) if index + 1 < len(names) else 0)
            for index, name in enumerate(names)}


def topology_nodes(geometry, marks):
    body, = (Ref(item.id) for item in geometry.bodies)
    interior = Ref(body.name + ":solid")
    exterior = Ref(body.name + ":void")
    solid_shell = Ref(body.name + ":solid-shell")
    void_shell = Ref(body.name + ":void-shell")
    points = {vertex.id: Ref(vertex.id + ":point") for vertex in geometry.vertices}
    first_face = Ref(geometry.faces[0].id)
    curve_owners = {edge.curve_id: Ref(edge.id) for edge in geometry.edges}
    surface_owners = {face.surface_id: Ref(face.id) for face in geometry.faces}
    nodes = [
        world(marks, body),
        DraftNode(body, 12, {"owner": Ref("world"), "shell": solid_shell, "region": exterior,
                             "edge": Ref(geometry.edges[0].id), "vertex": Ref(geometry.vertices[0].id),
                             "boundary_point": points[geometry.vertices[0].id], "boundary_curve": Ref(geometry.curves[0].id),
                             "boundary_surface": Ref(geometry.surfaces[0].id)}),
        DraftNode(exterior, 19, {"body": body, "next": interior, "previous": 0, "shell": void_shell, "type": "V"}),
        DraftNode(interior, 19, {"body": body, "next": 0, "previous": exterior, "shell": solid_shell, "type": "S"}),
        DraftNode(solid_shell, 13, {"body": body, "region": interior, "face": first_face, "front_face": 0}),
        DraftNode(void_shell, 13, {"body": 0, "region": exterior, "face": 0, "front_face": first_face}),
    ]
    face_links = chain(face.id for face in geometry.faces)
    use_map = {use.id: use for use in geometry.coedges}
    uses_by_edge = {}
    for use in geometry.coedges:
        uses_by_edge.setdefault(use.edge_id, []).append(use)
    edges = {edge.id: edge for edge in geometry.edges}
    loops = {loop.id: loop for loop in geometry.loops}
    for face in geometry.faces:
        loop_id, = face.loop_ids
        loop = loops[loop_id]
        previous, following = face_links[face.id]
        nodes.extend((
            DraftNode(Ref(face.id), 14, {"shell": solid_shell, "front_shell": void_shell,
                                        "loop": Ref(loop_id), "surface": Ref(face.surface_id),
                                        "previous": previous, "next": following, "previous_front": previous,
                                        "next_front": following, "next_on_surface": 0, "previous_on_surface": 0,
                                        "sense": "+" if face.same_sense else "-"}),
            DraftNode(Ref(loop_id), 15, {"face": Ref(face.id), "halfedge": Ref(loop.coedge_ids[0]), "next": 0}),
        ))
        ids = loop.coedge_ids
        for at, key in enumerate(ids):
            use = use_map[key]
            edge = edges[use.edge_id]
            mate, = (entry for entry in uses_by_edge[edge.id] if entry is not use)
            finish = edge.start_vertex_id if use.reversed else edge.end_vertex_id
            nodes.append(DraftNode(Ref(key), 17, {
                "edge": Ref(edge.id), "other": Ref(mate.id), "vertex": Ref(finish), "loop": Ref(loop_id),
                "forward": Ref(ids[(at + 1) % len(ids)]), "backward": Ref(ids[at - 1]),
                "sense": "-" if use.reversed else "+", "curve": 0,
            }))
    for edge in geometry.edges:
        nodes.append(DraftNode(Ref(edge.id), 16, {
            "owner": body, "curve": Ref(edge.curve_id), "halfedge": Ref(uses_by_edge[edge.id][0].id),
            "next_on_curve": 0, "previous_on_curve": 0,
        }))
    for vertex in geometry.vertices:
        nodes.extend((DraftNode(Ref(vertex.id), 18, {"point": points[vertex.id], "owner": body}),
                      DraftNode(points[vertex.id], 29, {"pvec": metres(vertex.point), "owner": Ref(vertex.id)})))
    for curve in geometry.curves:
        nodes.append(DraftNode(Ref(curve.id), 30, {"pvec": metres(curve.origin), "direction": vector(curve.direction),
                                                   "owner": curve_owners[curve.id], "sense": "+"}))
    for surface in geometry.surfaces:
        nodes.append(DraftNode(Ref(surface.id), 50, {"pvec": metres(surface.origin), "normal": vector(surface.normal),
                                                   "x_axis": vector(surface.reference_direction), "sense": "+",
                                                   "owner": surface_owners[surface.id]}))
    return tuple(nodes)


def plan_rectangle(child, session):
    require(not child.model["fd88"]["atoms"] and not child.model["ffe0"] and child.model["fe38"] is None
            and child.extrusion is not None and not child.extrusion.feature.f.get("has_f3d0"),
            "allocation requires a cache-free generated part and fresh atom manager")
    geometry, bounds, volume, area, roles = rectangle(child)
    marks = allocate_marks(session)
    updates = allocate_updates(session, child.model_header)
    tracking, archive = allocate_tracking(child, geometry, session, marks, updates)
    topology = topology_nodes(geometry, marks)
    return RectanglePlan(geometry, bounds, volume, area, roles, marks, tracking, archive, topology)
