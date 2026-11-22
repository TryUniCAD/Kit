from decimal import Decimal
from math import dist, isclose, isfinite
from EllipseModel import predict
from interchange.brep.Curves.BrepCurves import LineCurve, NurbsCurve
from interchange.brep.Curves.BrepPcurves import LinePcurve, NurbsPcurve
from interchange.brep.Surfaces.BrepSurfaces import NurbsSurface, PlaneSurface


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def compare_six(actual, expected, near_zero):
    require(isfinite(actual) and isfinite(expected), "non-finite native measurement comparison")
    tolerance = near_zero if abs(expected) < near_zero else float(Decimal(5).scaleb(Decimal(str(expected)).adjusted() - 6))
    return abs(actual - expected) <= tolerance


def xyz(vector):
    return vector.x, vector.y, vector.z


def quadratic(points, weights, station):
    quarter = min(int(station), 3)
    step = station - quarter
    basis = ((1 - step) ** 2, 2 * step * (1 - step), step ** 2)
    weighted = [value * weight for value, weight in zip(basis, weights[2 * quarter:2 * quarter + 3], strict=True)]
    return tuple(sum(value * factor for value, factor in zip(axis, weighted, strict=True)) / sum(weighted)
                 for axis in zip(*points[2 * quarter:2 * quarter + 3], strict=True))


def point_on_curve(curve, parameter):
    if isinstance(curve, LineCurve):
        return tuple(coord + parameter * unit for coord, unit in zip(xyz(curve.origin), xyz(curve.direction), strict=True))
    require(isinstance(curve, NurbsCurve) and curve.degree == 2 and not curve.periodic,
            "closed conic lacks exact rational intervals")
    return quadratic(tuple(xyz(point) for point in curve.control_points), curve.weights, parameter)


def point_on_trim(trim, parameter):
    if isinstance(trim, LinePcurve):
        return (trim.origin.x + parameter * trim.direction.x, trim.origin.y + parameter * trim.direction.y)
    require(isinstance(trim, NurbsPcurve) and trim.degree == 2 and not trim.periodic,
            "planar cap lacks an exact rational trim")
    return quadratic(tuple((point.x, point.y) for point in trim.control_points), trim.weights, parameter)


def point_on_face(surface, uv):
    first, second = uv
    if isinstance(surface, PlaneSurface):
        major = xyz(surface.reference_direction)
        require(surface.normal.x == surface.normal.y == 0 and abs(surface.normal.z) == 1, "cap has a wrong support normal")
        minor = (-major[1] * surface.normal.z, major[0] * surface.normal.z, 0.0)
        return tuple(value + first * axis + second * orthogonal
                     for value, axis, orthogonal in zip(xyz(surface.origin), major, minor, strict=True))
    require(isinstance(surface, NurbsSurface) and (surface.degree_u, surface.degree_v) == (2, 1)
            and not surface.periodic_u and not surface.periodic_v and surface.knots_u == (0., 1., 2., 3., 4.)
            and surface.multiplicities_u == (3, 2, 2, 2, 3) and surface.multiplicities_v == (2, 2)
            and all(row[0] == row[1] > 0 for row in surface.weights),
            "lifted conic has a wrong tensor basis")
    height = second / surface.knots_v[-1]
    controls = tuple(tuple((1 - height) * a + height * b for a, b in zip(xyz(lower), xyz(upper), strict=True))
                     for lower, upper in surface.control_points)
    return quadratic(controls, tuple(row[0] for row in surface.weights), first)


def require_ellipse(point, prediction):
    center, major, minor = prediction["points_m"][0], *prediction["unit_axes"]
    dx, dy = point[0] / 1000 - center[0], point[1] / 1000 - center[1]
    radius_a, radius_b = prediction["radii_m"]
    value = ((dx * major[0] + dy * major[1]) / radius_a) ** 2 + ((dx * minor[0] + dy * minor[1]) / radius_b) ** 2
    require(isclose(value, 1., rel_tol=0., abs_tol=2e-13), "sweep point is not on the independently authored ellipse")


def check_shell(document, prediction):
    brep = document.brep
    body, = document.bodies
    require(brep is not None and not document.brep_payloads and not brep.validate(frozenset((body.id,))),
            "typed ellipse did not supply valid owned neutral B-rep")
    require(tuple(map(len, (brep.bodies, brep.regions, brep.shells, brep.faces, brep.edges, brep.vertices, brep.pcurves)))
            == (1, 1, 1, 3, 3, 2, 6) and brep.bodies[0].design_body_id == body.id and brep.shells[0].closed,
            "elliptic solid sew or body owner differs")
    curves, surfaces, edges, trims, coedges, loops, vertices = (
        {node.id: node for node in group} for group in
        (brep.curves, brep.surfaces, brep.edges, brep.pcurves, brep.coedges, brep.loops, brep.vertices)
    )
    uses = {}
    evaluations = 0
    for face in brep.faces:
        loop = loops[face.loop_ids[0]]
        require(len(face.loop_ids) == 1 and face.same_sense and loop.outer, "incorrect closure or face orientation")
        surface = surfaces[face.surface_id]
        rows = [coedges[key] for key in loop.coedge_ids]
        ends = []
        for coedge in rows:
            edge, trim = edges[coedge.edge_id], trims[coedge.pcurve_id]
            uses.setdefault(edge.id, []).append(coedge.reversed)
            curve = curves[edge.curve_id]
            parameter = edge.end_parameter - edge.start_parameter
            for index in range(17):
                model = point_on_curve(curve, edge.start_parameter + index * parameter / 16)
                expected = point_on_face(surface, point_on_trim(trim, edge.start_parameter + index * parameter / 16))
                require_ellipse(model, prediction)
                require(dist(model, expected) < 1e-11, "trim and its physical edge disagree")
                evaluations += 1
            for key, value in ((edge.start_vertex_id, edge.start_parameter), (edge.end_vertex_id, edge.end_parameter)):
                require(dist(xyz(vertices[key].point), point_on_curve(curve, value)) < 1e-11,
                        "closed elliptic edge is not anchored to the actual seam")
            begin = edge.end_parameter if coedge.reversed else edge.start_parameter
            finish = edge.start_parameter if coedge.reversed else edge.end_parameter
            ends.append((point_on_trim(trim, begin), point_on_trim(trim, finish)))
        require(all(dist(a[1], b[0]) < 1e-11 for a, b in zip(ends, ends[1:] + ends[:1], strict=True)),
                "face boundary is not closed in parameter space")
        if isinstance(surface, NurbsSurface):
            for heading in range(33):
                for fraction in (.25, .5, .75):
                    height = surface.knots_v[-1] * fraction
                    point = point_on_face(surface, (heading / 8, height))
                    require(isclose(point[2], height, abs_tol=1e-12), "sweep changes the axial station")
                    require_ellipse(point, prediction)
                    evaluations += 1
    require(all(sorted(value) == [False, True] for value in uses.values()), "closed sweep is not oppositely sewn")
    return evaluations


def check_measures(document, case, native):
    intended = predict(case)
    topology = document.bodies[0].topology
    measures = topology.volume * 1e-9, topology.surface_area * 1e-6
    nominal = intended["states"][0]
    xyz_bounds = (xyz(topology.bounding_box.minimum), xyz(topology.bounding_box.maximum))
    bounds = tuple(tuple(point[index] / 1000 for point in xyz_bounds) for index in range(3))
    require(all(isclose(a, b, rel_tol=2e-13) for a, b in zip(measures, (nominal["volume_m3"], nominal["area_m2"]), strict=True))
            and all(dist(a, b) <= 1e-15 for a, b in zip(bounds, nominal["bounds_m"], strict=True)),
            "analytic solid measurements disagree with independent predictions")
    axes = intended["unit_axes"]
    caps = [surface for surface in document.brep.surfaces if isinstance(surface, PlaneSurface)]
    center = tuple((left + right) * .5e-3 for left, right in zip(xyz(caps[0].origin), xyz(caps[1].origin), strict=True))
    require(dist(center, nominal["com_m"]) <= 1e-15
            and [plane.normal.z for plane in caps] == [-1., 1.]
            and all(dist(xyz(plane.reference_direction), axes[0]) < 1e-14 for plane in caps),
            "retained cap axis or inferred uniform centroid disagrees with the neutral input")
    vertices = sorted((tuple(value / 1000 for value in xyz(node.point)) for node in document.brep.vertices), key=lambda row: row[2])
    require(native["solid_count"] == topology.solid_count and native["faces"] == topology.face_count
            and native["accuracy_level"] == 2, "cold native body or high accuracy comparison scope differs")
    actual = (*measures, *center, *(item for row in bounds for item in row), *(item for row in vertices for item in row))
    observed = (native["volume"], native["area"], *native["com"], *(item for row in native["bounds_m"] for item in row),
                *(item for row in native["seams_m"] for item in row))
    require(all(compare_six(a, b, 1e-11) for a, b in zip(actual, observed, strict=True)),
            "neutral solid did not meet six significant figures against native observations")
    return check_shell(document, intended), len(observed)
