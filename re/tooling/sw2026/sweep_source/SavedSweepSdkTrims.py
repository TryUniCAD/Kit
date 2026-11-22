from math import cos, dist, pi, sin, ulp

from interchange.brep.Curves.BrepPcurves import CirclePcurve, LinePcurve
from interchange.brep.Surfaces.BrepSurfaces import PlaneSurface, TorusSurface
from AuditSavedSweepMain import demand


def xyz(value):
    return value.x, value.y, value.z


def scale(vector, factor):
    return tuple(item * factor for item in vector)


def add(first, second):
    return tuple(a + b for a, b in zip(first, second, strict=True))


def cross(first, second):
    x, y, z = first
    a, b, c = second
    return y * c - z * b, z * a - x * c, x * b - y * a


def ring_point(center, normal, first, radius, angle):
    return add(center, scale(add(scale(first, cos(angle)), scale(cross(normal, first), sin(angle))), radius))


def wall_point(surface, u, v):
    center = add(xyz(surface.center), scale(xyz(surface.axis), surface.minor_radius * sin(v)))
    radius = surface.major_radius + surface.minor_radius * cos(v)
    return ring_point(center, xyz(surface.axis), xyz(surface.reference_direction), radius, u)


def typed_index(value):
    return int(value.id.split(":")[-1]) - 1


def check_trims(model, geometry, design_body_id):
    demand(not model.validate(frozenset((design_body_id,))) and model.bodies[0].design_body_id == design_body_id
           and len(model.pcurves) == 4 and len(model.vertices) == 2
           and all(vertex.attributes["periodic_seam"] is True for vertex in model.vertices),
           "the derived pcurves or periodic seam anchor lost actual portable ownership")
    (surface,) = (value for value in model.surfaces if type(value) is TorusSurface)
    uses = {typed_index(value): value for value in model.coedges}
    curves = {value.id: value for value in model.curves}
    edges = {value.id: value for value in model.edges}
    pcurves = {value.id: value for value in model.pcurves}
    surfaces = {value.id: value for value in model.surfaces}
    faces = {typed_index(value): value for value in model.faces}
    observations = []
    for rim in geometry["signed_rims"]:
        cap_use, wall_use = uses[rim["cap_fin"]], uses[rim["side_fin"]]
        circle = curves[edges[cap_use.edge_id].curve_id]
        wall_uv, cap_uv = pcurves[wall_use.pcurve_id], pcurves[cap_use.pcurve_id]
        plane = surfaces[faces[rim["cap_face"]].surface_id]
        demand(type(wall_uv) is LinePcurve and type(cap_uv) is CirclePcurve and type(plane) is PlaneSurface
               and cap_use.edge_id == wall_use.edge_id and cap_use.reversed != wall_use.reversed
               and wall_uv.direction.y == rim["curve_to_torus_v"]
               and wall_uv.direction.y * (-1 if wall_use.reversed else 1) == rim["wall_fin_dv"]
               and (-1 if cap_use.reversed else 1) == rim["cap_fin_dangle"]
               and wall_uv.origin.x == rim["u"] and wall_uv.origin.y == rim["v_at_curve_zero"],
               "portable pcurves lost the real saved signed fin orientation")
        for sample in range(4):
            theta = sample * pi / 2
            point = ring_point(xyz(circle.center), xyz(circle.axis), xyz(circle.reference_direction), circle.radius, theta)
            cap_point = ring_point(xyz(plane.origin), xyz(plane.normal), xyz(plane.reference_direction), cap_uv.radius, theta)
            trim_point = wall_point(surface, wall_uv.origin.x, wall_uv.origin.y + theta * wall_uv.direction.y)
            tolerance = 128 * ulp(surface.major_radius)
            demand(dist(point, cap_point) <= tolerance and dist(point, trim_point) <= tolerance,
                   "portable cap or wall parameter curve leaves its actual saved rim")
        observations.append({"physical_edge": rim["edge"], "cap_fin": rim["cap_fin"], "wall_fin": rim["side_fin"],
                             "u": wall_uv.origin.x, "phase": wall_uv.origin.y, "oriented_dv": rim["wall_fin_dv"],
                             "oriented_cap_angle": rim["cap_fin_dangle"], "verified_quarter_points": 4})
    return observations
