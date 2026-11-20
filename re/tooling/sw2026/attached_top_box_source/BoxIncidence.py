from collections import Counter
from itertools import combinations, product
from math import dist, isclose

from interchange.brep.Curves.BrepCurves import LineCurve
from interchange.brep.Surfaces.BrepSurfaces import PlaneSurface
from interchange.geometry.Models.Transform import KTransformIdentity


TOLERANCE_MM = 1e-10
CORNERS = tuple(product((0, 1), repeat=3))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def xyz(vector):
    return vector.x, vector.y, vector.z


def subtract(left, right):
    return tuple(a - b for a, b in zip(left, right, strict=True))


def dot(left, right):
    return sum(a * b for a, b in zip(left, right, strict=True))


def cross(left, right):
    i, j, k = left
    x, y, z = right
    return j*z-k*y, k*x-i*z, i*y-j*x


def edge_key(first, second):
    return tuple(sorted((first, second)))


def box_edges():
    return {edge_key(i, j) for i, j in combinations(range(8), 2)
            if sum(a != b for a, b in zip(CORNERS[i], CORNERS[j], strict=True)) == 1}


def use_faces(model, design_id):
    require(not model.validate(frozenset((design_id,)) if design_id else frozenset()),
            "decoded boundary is invalid")
    solid, = model.bodies
    region, = model.regions
    use, = model.shell_uses
    shell, = model.shells
    require(solid.region_ids == (region.id,) and not (solid.wire_ids or solid.vertex_ids or model.wires)
            and solid.design_body_id == design_id and solid.transform == KTransformIdentity
            and region.solid and region.shell_use_ids == (use.id,) and use.shell_id == shell.id and shell.closed
            and set(shell.face_use_ids) == {row.id for row in model.face_uses}
            and {row.face_id for row in model.face_uses} == {row.id for row in model.faces}
            and len(model.face_uses) == len(model.faces) == 6,
            "solid region, shell, face or body owner differs")
    return solid


def read_corners(model, expected):
    corner_ids = {}
    for vertex in model.vertices:
        locations = [n for n, point in enumerate(expected) if dist(xyz(vertex.point), point) <= TOLERANCE_MM]
        require(len(locations) == 1, "boundary vertex has no unique independently modeled box corner")
        corner_ids[vertex.id] = locations[0]
    require(len(model.vertices) == len(corner_ids) == 8 and set(corner_ids.values()) == set(range(8)),
            "box corners are incomplete or aliased")
    return corner_ids


def read_edges(model, corner_ids, expected):
    curves = {row.id: row for row in model.curves}
    edges = {}
    for edge in model.edges:
        first, second = (corner_ids[key] for key in (edge.start_vertex_id, edge.end_vertex_id))
        curve = curves[edge.curve_id]
        require(type(curve) is LineCurve and not edge.degenerate, "box edge has another geometric type")
        direction = xyz(curve.direction)
        require(isclose(dot(direction, direction), 1.0, rel_tol=0.0, abs_tol=TOLERANCE_MM)
                and all(dist(cross(direction, subtract(expected[key], xyz(curve.origin))), (0, 0, 0))
                        <= TOLERANCE_MM for key in (first, second)),
                "line carrier does not contain its independent endpoints")
        edges[edge.id] = (first, second)
    require(len(model.edges) == len(edges) == 12 and set(edge_key(*pair) for pair in edges.values()) == box_edges()
            and {row.curve_id for row in model.edges} == set(curves),
            "edge incidence differs from the independent box graph")
    return edges


def read_faces(model, edges, expected):
    loops = {row.id: row for row in model.loops}
    coedges = {row.id: row for row in model.coedges}
    planes = {row.id: row for row in model.surfaces}
    uses = Counter()
    incidence = {}
    for face in model.faces:
        loop_id, = face.loop_ids
        loop, plane = loops[loop_id], planes[face.surface_id]
        require(loop.outer and len(loop.coedge_ids) == 4 and type(plane) is PlaneSurface,
                "box face is not one planar outer ring of four edges")
        pairs = []
        for key in loop.coedge_ids:
            link = coedges[key]
            ends = edges[link.edge_id]
            pairs.append(ends[::-1] if link.reversed else ends)
            uses[key] += 1
        points = {a for a, _ in pairs}
        require(len(points) == 4 and all(a[1] == b[0] for a, b in zip(pairs, pairs[1:] + pairs[:1], strict=True)),
                "face contains a disconnected or repeated corner")
        side = tuple(sorted(points))
        normal = xyz(plane.normal)
        require(side not in incidence and isclose(dot(normal, normal), 1.0, rel_tol=0.0, abs_tol=TOLERANCE_MM)
                and all(abs(dot(normal, subtract(expected[key], xyz(plane.origin)))) <= TOLERANCE_MM for key in side),
                "box face lost its unique plane and incident corners")
        incidence[side] = sorted(edge_key(*pair) for pair in pairs)
    sides = {tuple(i for i, corner in enumerate(CORNERS) if corner[axis] == bit)
             for axis, bit in product(range(3), (0, 1))}
    use_counts = Counter(edge for ring in incidence.values() for edge in ring)
    require(set(incidence) == sides and use_counts == Counter({edge: 2 for edge in box_edges()})
            and uses == Counter({key: 1 for key in coedges})
            and {row.loop_ids[0] for row in model.faces} == set(loops)
            and {row.surface_id for row in model.faces} == set(planes),
            "face, loop or edge use inventory differs from the closed box")
    return incidence


def box_incidence(model, expected, design_id=""):
    solid = use_faces(model, design_id)
    corners = read_corners(model, expected)
    edges = read_edges(model, corners, expected)
    faces = read_faces(model, edges, expected)
    return solid.id, {
        "edges": sorted(edge_key(*pair) for pair in edges.values()),
        "faces": sorted(faces.items()),
        "counts": [1, 1, len(faces), len(edges), len(corners), len(model.coedges)],
    }
