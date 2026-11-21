from itertools import product
from math import cos, isclose, pi, radians, sin

from interchange.brep.Curves.BrepCurves import CircleCurve
from interchange.brep.Surfaces.BrepSurfaces import CylinderSurface, PlaneSurface


def xyz(value):
    return value.x, value.y, value.z


def close(left, right):
    return isclose(left, right, rel_tol=1e-12, abs_tol=1e-10)


def same_point(left, right):
    return all(close(a, b) for a, b in zip(left, right, strict=True))


def compare_corners(actual, expected):
    remaining = list(actual)
    for corner in expected:
        found = [point for point in remaining if same_point(point, corner)]
        assert len(found) == 1, (corner, remaining)
        remaining.remove(found[0])
    assert not remaining, remaining


def authored_sector(spec):
    first = radians(spec["angle_deg"])
    second = radians(spec["second_deg"])
    start, end = {
        "single": (0, first),
        "midplane": (-first / 2, first / 2),
        "two": (-second, first),
    }[spec["mode"]]
    assert spec["plane"] == "top"
    x0 = spec["axis_x_m"] * 1000.0
    handedness = 1 if spec["reverse"] else -1
    ri, ro = [1000.0 * value for value in spec["radius_m"]]
    lo, hi = [1000.0 * value for value in reversed(spec["axial_m"])]
    lo, hi = -lo, -hi

    def point(angle, radius, axial):
        return x0 + radius * cos(angle), handedness * radius * sin(angle), axial

    caps = tuple(point(*row) for row in product((start, end), (ri, ro), (lo, hi)))
    extrema = [start, end] + [
        k * pi / 2 for k in range(-4, 5) if start < k * pi / 2 < end
    ]
    sweep_points = tuple(point(*row) for row in product(extrema, (ri, ro), (lo, hi)))
    coordinates = tuple(zip(*sweep_points, strict=True))
    bounds = (tuple(map(min, coordinates)), tuple(map(max, coordinates)))
    span = end - start
    mean_radius = (2 / 3) * (ro**3 - ri**3) / (ro**2 - ri**2)
    return {
        "interval_radians": (start, end),
        "radii_mm": (ri, ro),
        "caps_mm": caps,
        "bounds_mm": bounds,
        "volume_mm3": span * (hi - lo) * (ro**2 - ri**2) / 2,
        "area_mm2": span * ((ro + ri) * (hi - lo) + ro**2 - ri**2)
        + 2 * (hi - lo) * (ro - ri),
        "centre_mm": (
            x0 + mean_radius * (sin(end) - sin(start)) / span,
            handedness * mean_radius * (cos(start) - cos(end)) / span,
            (lo + hi) / 2,
        ),
    }


def check_brep(model, identity, expected):
    assert model is not None
    (body,) = model.bodies
    assert body.design_body_id == identity and not model.validate(
        frozenset((identity,))
    )
    assert (
        len(model.shells),
        len(model.faces),
        len(model.edges),
        len(model.vertices),
    ) == (1, 6, 12, 8)
    assert sum(type(surface) is PlaneSurface for surface in model.surfaces) == 4
    radii = sorted(
        surface.radius for surface in model.surfaces if type(surface) is CylinderSurface
    )
    assert same_point(radii, expected["radii_mm"])
    compare_corners(
        tuple(xyz(vertex.point) for vertex in model.vertices), expected["caps_mm"]
    )
    orbits = {curve.id for curve in model.curves if type(curve) is CircleCurve}
    edges = [edge for edge in model.edges if edge.curve_id in orbits]
    lower, upper = expected["interval_radians"]
    assert len(edges) == len(orbits) == 4
    assert all(
        close(abs(edge.end_parameter - edge.start_parameter), upper - lower)
        for edge in edges
    )


def check_measures(topology, expected, native):
    assert (
        topology.solid_count,
        topology.shell_count,
        topology.face_count,
        topology.edge_count,
        topology.vertex_count,
    ) == (1, 1, 6, 12, 8)
    assert close(topology.volume, expected["volume_mm3"])
    assert close(topology.surface_area, expected["area_mm2"])
    bounds = topology.bounding_box
    assert same_point(xyz(bounds.minimum), expected["bounds_mm"][0])
    assert same_point(xyz(bounds.maximum), expected["bounds_mm"][1])
    measure = native["mass"]
    assert close(topology.volume, measure["volume"] * 1e9)
    assert close(topology.surface_area, measure["area"] * 1e6)
    assert same_point(
        expected["centre_mm"], tuple(item * 1000.0 for item in measure["com"])
    )
