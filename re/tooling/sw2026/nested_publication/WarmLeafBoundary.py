from dataclasses import replace
from itertools import product
from math import fsum, hypot, isclose

from BuildLocalBodyKernel import cross, difference, dot
from ProjectDisclosedImport import coordinates, rectangular_boundary, require
from interchange import PlaneSurface
from interchange.geometry.Models.VectorSpace import SpaceVector


def orient_saved_planes(model, body_id):
    require(model is not None and not model.validate(frozenset((body_id,))),
            "stored geometry must have one validated public body correspondence")
    surfaces = {row.id: row for row in model.surfaces}
    require(len(model.faces) == len(surfaces) == 6
            and {row.surface_id for row in model.faces} == set(surfaces)
            and all(type(row) is PlaneSurface for row in surfaces.values()),
            "warm leaf requires six uniquely used planar carriers")
    aligned = []
    changed = []
    for face in model.faces:
        surface = surfaces[face.surface_id]
        if not face.same_sense:
            normal = SpaceVector(*(-word for word in coordinates(surface.normal)))
            surface = replace(surface, normal=normal)
            changed.append(face.id)
        aligned.append(surface)
    view = replace(model, surfaces=tuple(aligned),
                   faces=tuple(replace(face, same_sense=True) for face in model.faces))
    return view, changed


def oriented_rings(model):
    edges = {row.id: row for row in model.edges}
    vertices = {row.id: coordinates(row.point) for row in model.vertices}
    loops = {row.id: row for row in model.loops}
    coedges = {row.id: row for row in model.coedges}
    for face in model.faces:
        loop = loops[face.loop_ids[0]]
        ring = []
        for identifier in loop.coedge_ids:
            row = coedges[identifier]
            edge = edges[row.edge_id]
            end = edge.end_vertex_id if row.reversed else edge.start_vertex_id
            ring.append(vertices[end])
        yield tuple(ring)


def polyhedral_integrals(model, centre):
    areas, volumes, moments = [], [], [[], [], []]
    for first, second, third, fourth in oriented_rings(model):
        for left, right in ((second, third), (third, fourth)):
            area = hypot(*cross(difference(left, first), difference(right, first))) / 2
            volume = dot(difference(first, centre), cross(difference(left, centre), difference(right, centre))) / 6
            require(area > 0 and volume > 0, "oriented shell contains a reversed or degenerate triangle")
            areas.append(area)
            volumes.append(volume)
            for axis in range(3):
                moments[axis].append(fsum(p[axis] for p in (centre, first, left, right)) * volume / 4)
    volume = fsum(volumes)
    return volume, fsum(areas), tuple(fsum(axis) / volume for axis in moments)


def analytic(vertices, depth):
    left, bottom = vertices[0]
    right, top = vertices[2]
    require(tuple(vertices) == ((left, bottom), (right, bottom), (right, top), (left, top))
            and min(right - left, top - bottom, depth) > 0,
            "sketch and depth must form the exact forward principal rectangle")
    width, height = right - left, top - bottom
    centre = ((left + right) / 2, (bottom + top) / 2, depth / 2)
    return (width, height, depth), ((left, right), (bottom, top), (0.0, depth)), (
        width * height * depth, 2 * (width * height + width * depth + height * depth), centre,
    )


def near(actual, expected, abs_tol=1e-10):
    return isclose(actual, expected, rel_tol=1e-12, abs_tol=abs_tol)


def measure_boundary(model, body_id, vertices, depth, native=None):
    require(model.bodies[0].design_body_id == body_id, "B-rep body has a different design owner")
    view, inverted = orient_saved_planes(model, body_id)
    boundary = rectangular_boundary(view, body_id)
    dimensions, limits, predicted = analytic(vertices, depth)
    expected_points = tuple(sorted(product(*limits)))
    require(all(all(near(a, b) for a, b in zip(source, expected, strict=True))
                for source, expected in zip(sorted(boundary.vertices), expected_points, strict=True)),
            "the eight actual solid corners differ from the authored live sketch extrusion")
    measured = polyhedral_integrals(model, predicted[2])
    flat = (*measured[:2], *measured[2])
    require(all(near(a, b) for a, b in zip(flat, (*predicted[:2], *predicted[2]), strict=True)),
            "oriented shell integrals differ from the independent parametric prism")
    peak = None
    if native is not None:
        values = (native["volume"] * 1e9, native["area"] * 1e6, *(coordinate * 1000 for coordinate in native["com"]))
        require(all(isclose(a, b, rel_tol=5e-7, abs_tol=1e-8)
                    for a, b in zip(flat, values, strict=True)),
                "oriented shell integrals differ from the exact prior native observation")
        peak = max(abs(a - b) for a, b in zip(flat, values, strict=True))
    return {"dimensions_mm": dimensions, "bounds_mm": boundary.limits, "volume_mm3": measured[0],
            "surface_area_mm2": measured[1], "centre_of_volume_mm": measured[2],
            "vertex_count": len(boundary.vertices), "edge_count": len(boundary.edges),
            "face_count": len(boundary.faces), "coedge_count": len(model.coedges),
            "inverted_carrier_count": len(inverted), "max_native_metric_delta_in_mm_units": peak}
