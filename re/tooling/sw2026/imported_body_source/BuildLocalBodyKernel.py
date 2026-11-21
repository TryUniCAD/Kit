from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import replace
from hashlib import sha256
from itertools import chain
import json
from math import fsum, hypot, isclose
from pathlib import Path
import platform
import sys
import zlib

from builders.EmptyPartition import PARTITION_KIND, PMARK_KIND, WORLD_KIND
from convert.Geometry.Extrude.Polygon.PolygonExtrude import BuildPrism
from convert.Geometry.Parasolid import DecodePartData, EncodePartData
from interchange.brep.Curves.BrepCurves import LineCurve
from interchange.brep.Surfaces.BrepSurfaces import PlaneSurface
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.brep.Validation.BrepValidate import GetBrepErrors
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorPlane import PlaneVector
from para.Partition import Node, SCHEMAS
from para.rectangle.Allocate import index_fields
from para.rectangle.Geometry import topology_nodes, vector
from para.rectangle.RectanglePartition import complete_topology
from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

from LocalBodyKernel import (
    ATTRIBUTE, ATTRIBUTE_LIST, BODY, DEFINITION, DEFINITION_NAME, EDGE, FACE, FIN, LOOP, POINT,
    POINTER_BLOCK, SLOT_TYPES, VERTEX, _render_local, active_ownership, decode_local, fingerprint,
    object_at, require, solid_ownership,
)


CASES = {
    "Rectangular": (((-9, 5), (4, 5), (4, 23), (-9, 23)), (3, 14),
                    (2574, 1150, (-2.5, 14, 8.5))),
    "Concave": (((7, -12), (33, -12), (33, -3), (17, -3), (17, 8), (7, 8)), (-4, 11),
                (5160, 2068, (6000 / 344, -1480 / 344, 3.5))),
}


def prism_model(name, points, levels):
    ring = tuple(PlaneVector(*value) for value in points)
    lines = tuple(LineGeometry(start, end) for start, end in zip(ring, ring[1:] + ring[:1], strict=True))
    model = BuildPrism(name, Transform(), lines, *levels)[0]
    body, = model.bodies
    return replace(model, bodies=(replace(body, design_body_id=""),))


def difference(left, right):
    return tuple(a - b for a, b in zip(left, right, strict=True))


def cross(left, right):
    a, b, c = left
    x, y, z = right
    return (b * z - c * y, c * x - a * z, a * y - b * x)


def dot(left, right):
    return fsum(a * b for a, b in zip(left, right, strict=True))


def face_rings(model):
    vertices = {vertex.id: vector(vertex.point) for vertex in model.vertices}
    edges = {edge.id: edge for edge in model.edges}
    coedges = {coedge.id: coedge for coedge in model.coedges}
    loops = {loop.id: loop for loop in model.loops}
    surfaces = {surface.id: surface for surface in model.surfaces}
    result = []
    for face in model.faces:
        loop, = (loops[identifier] for identifier in face.loop_ids)
        require(loop.outer and face.same_sense and len(loop.coedge_ids) >= 3,
                "local prism needs one outward outer loop per face")
        uses = tuple(coedges[identifier] for identifier in loop.coedge_ids)
        boundary = tuple(vertices[edges[use.edge_id].end_vertex_id if use.reversed else edges[use.edge_id].start_vertex_id]
                         for use in uses)
        surface = surfaces[face.surface_id]
        normal = vector(surface.normal)
        origin = vector(surface.origin)
        require(all(abs(dot(difference(point, origin), normal)) <= 1e-9 for point in boundary),
                "local prism trim leaves its supporting plane")
        oriented_area = fsum(dot(cross(difference(left, boundary[0]), difference(right, boundary[0])), normal)
                             for left, right in zip(boundary[1:-1], boundary[2:], strict=True))
        require(oriented_area > 0, "local prism face normal contradicts its oriented outer loop")
        result.append(boundary)
    return tuple(result)


def canonical_face(ring):
    offset = ring.index(min(ring))
    return ring[offset:] + ring[:offset]


def require_neutral_prism(model):
    require(type(model) is BrepModel and model.schema_version == "1.0", "local prism requires a typed neutral B-rep")
    errors = GetBrepErrors(model, frozenset())
    require(not errors, "invalid neutral B-rep: " + "; ".join(errors))
    require((len(model.bodies), len(model.regions), len(model.shells), len(model.shell_uses)) == (1, 1, 1, 1)
            and not model.wires and not model.pcurves, "local prism requires one region and no wires or pcurves")
    body, region, shell, shell_use = model.bodies[0], model.regions[0], model.shells[0], model.shell_uses[0]
    require(body.transform == Transform() and not (body.design_body_id or body.wire_ids or body.vertex_ids)
            and region.solid and shell.closed and not shell_use.reversed
            and all(not use.reversed for use in model.face_uses), "unsupported local body or ownership semantics")
    require(tuple(use.face_id for use in model.face_uses) == tuple(face.id for face in model.faces)
            and shell.face_use_ids == tuple(use.id for use in model.face_uses), "unsupported face use order")
    entities = chain(model.curves, model.surfaces, model.vertices, model.edges, model.coedges, model.loops,
                     model.faces, model.face_uses, model.shells, model.shell_uses, model.regions, model.bodies)
    require(all(not (entity.attributes or entity.provenance) for entity in entities),
            "local geometry-only prism does not admit source attributes or provenance")
    require(all(type(curve) is LineCurve for curve in model.curves)
            and all(type(surface) is PlaneSurface for surface in model.surfaces),
            "local prism needs exact line curves and planar faces")
    require({edge.curve_id for edge in model.edges} == {curve.id for curve in model.curves}
            and len(model.edges) == len(model.curves)
            and {face.surface_id for face in model.faces} == {surface.id for surface in model.surfaces}
            and len(model.faces) == len(model.surfaces), "local prism needs one analytic carrier per edge or face")
    require(all(len(face.loop_ids) == 1 for face in model.faces)
            and len(model.faces) == len(model.loops)
            and not any(item.tolerance for item in chain(model.vertices, model.edges, model.faces))
            and not any(edge.degenerate for edge in model.edges), "local prism requires unmodified topology and tolerances")
    vertices = {item.id: vector(item.point) for item in model.vertices}
    curves = {item.id: item for item in model.curves}
    for edge in model.edges:
        line = curves[edge.curve_id]
        start = vector(line.origin)
        unit = vector(line.direction)
        require(isclose(hypot(*unit), 1, rel_tol=0, abs_tol=1e-12), "local line direction is not unit length")
        for identifier, parameter in ((edge.start_vertex_id, edge.start_parameter), (edge.end_vertex_id, edge.end_parameter)):
            actual = tuple(a + parameter * b for a, b in zip(start, unit, strict=True))
            require(hypot(*difference(actual, vertices[identifier])) <= 1e-9, "local edge trim does not reach its vertex")
    rings = face_rings(model)
    levels = tuple(sorted({point[2] for point in vertices.values()}))
    require(len(levels) == 2, "local prism requires two parallel XY section levels")
    lower = tuple(ring for ring in rings if all(point[2] == levels[0] for point in ring))
    require(len(lower) == 1, "local prism has no unique lower section")
    section = tuple(point[:2] for point in lower[0])
    comparison = prism_model("SectionWitness", section, levels)
    require(tuple(sorted(map(canonical_face, rings))) == tuple(sorted(map(canonical_face, face_rings(comparison)))),
            "neutral faces do not form the exact prism of their lower section")


def make_nodes(model):
    require_neutral_prism(model)
    draft, next_id = complete_topology(topology_nodes(model, None))
    indexes = {node.ref: index for index, node in enumerate(draft, 1)}
    require(len(indexes) == len(draft) and draft[0].kind == BODY, "local kernel allocation requires one root BODY")
    nodes = []
    for item in draft:
        fields = index_fields(item.fields, indexes)
        if item.kind == BODY:
            fields.update(highest_node_id=next_id - 1, attributes_features=0, attribute_chains=0)
        nodes.append(Node(indexes[item.ref], item.kind, fields))
    return tuple(nodes)


def require_closed_unattributed(nodes):
    body = nodes[0]
    indexed = {node.index: node for node in nodes}
    forbidden = {WORLD_KIND, PARTITION_KIND, PMARK_KIND, ATTRIBUTE_LIST, POINTER_BLOCK,
                 DEFINITION_NAME, DEFINITION, ATTRIBUTE, *SLOT_TYPES.values()}
    require(len(indexed) == len(nodes) and all(index > 0 for index in indexed)
            and body.kind == BODY and body.fields["owner"] == 0
            and sum(node.kind == BODY for node in nodes) == 1
            and not any(node.kind in forbidden for node in nodes), "local kernel must have only a bare BODY")
    require(not any(node.fields.get("attributes_features") or node.fields.get("attribute_chains") for node in nodes),
            "bare local kernel has populated attribute pointers")
    require(not active_ownership(indexed, body), "bare local kernel has a nonresident pointer")
    solid_ownership(indexed, body)
    return indexed


def face_points(nodes, face):
    loop_node = object_at(nodes, face.fields["loop"], LOOP)
    head = loop_node.fields["halfedge"]
    points, seen = [], set()
    current = head
    while current not in seen:
        seen.add(current)
        fin = object_at(nodes, current, FIN)
        require(fin.fields["loop"] == loop_node.index, "local fin escaped its owning loop")
        vertex = object_at(nodes, fin.fields["vertex"], VERTEX)
        point = object_at(nodes, vertex.fields["point"], POINT)
        points.append(point.fields["pvec"])
        current = fin.fields["forward"]
    require(current == head and len(points) >= 3, "local finite face ring does not close")
    return points


def boundary_measures(nodes):
    areas, volumes, moments = [], [], []
    for face in nodes.values():
        if face.kind != FACE:
            continue
        corner, *ring = face_points(nodes, face)
        normals = []
        for left, right in zip(ring[:-1], ring[1:], strict=True):
            normals.append(cross(difference(left, corner), difference(right, corner)))
            volume = dot(corner, cross(left, right)) / 6
            volumes.append(volume)
            moments.append(tuple(volume * fsum(axis) / 4 for axis in zip(corner, left, right, strict=True)))
        areas.append(hypot(*(fsum(axis) for axis in zip(*normals, strict=True))) / 2)
    volume = fsum(volumes)
    require(volume > 0, "bare BODY triangles do not enclose a positive oriented volume")
    points = tuple(node.fields["pvec"] for node in nodes.values() if node.kind == POINT)
    axes = tuple(zip(*points, strict=True))
    return {
        "volume_m3": volume,
        "area_m2": fsum(areas),
        "centroid_m": tuple(fsum(axis) / volume for axis in zip(*moments, strict=True)),
        "bounds_m": tuple(tuple(extreme(axis) for axis in axes) for extreme in (min, max)),
    }


def measure_case(name, case):
    points, levels, analytic = case
    model = prism_model(name, points, levels)
    nodes = make_nodes(model)
    require_closed_unattributed(nodes)
    raw = _render_local(nodes)
    decoded, _ = decode_local(raw)
    indexed = require_closed_unattributed(decoded)
    require(decoded == nodes and _render_local(decoded) == raw, "local typed round trip differs")
    framed = EncodePartData(raw)
    payload, = DecodePartData(framed)
    require(payload.data == raw and payload.stored_size == len(framed), "local compression round trip differs")
    counts = Counter(node.kind for node in decoded)
    require((counts[VERTEX], counts[EDGE], counts[FACE]) == (len(model.vertices), len(model.edges), len(model.faces)),
            "bare BODY changed neutral topology counts")
    measured = boundary_measures(indexed)
    volume, area, centroid = analytic
    expected = {"volume_m3": volume / 1e9, "area_m2": area / 1e6, "centroid_m": tuple(value / 1000 for value in centroid)}
    require(all(isclose(measured[name], expected[name], rel_tol=2e-12) for name in ("volume_m3", "area_m2"))
            and all(isclose(a, b, rel_tol=2e-12, abs_tol=1e-16)
                    for a, b in zip(measured["centroid_m"], expected["centroid_m"], strict=True)),
            "bare BODY geometry disagrees with the independent neutral measures")
    return (raw, framed, {
        "neutral_xy_mm": points, "neutral_z_mm": levels,
        "raw": fingerprint(raw), "wrapper": fingerprint(framed), "attributes": 0, "nonresident_links": 0,
        "resident_node_kinds": {SCHEMAS[kind].name: count for kind, count in sorted(counts.items())},
        "bare_body_owner": nodes[0].fields["owner"], "expected_si": expected, "decoded_si": measured,
        "typed_roundtrip_exact": True, "wrapper_roundtrip_exact": True,
    })


def build_batch():
    kernel_dir = Path(__file__).resolve().parent
    audit = BuildAudit(kernel_dir)
    audit.BeginBuild()
    enabled = True

    def guard(event, arguments):
        if enabled:
            audit.InspectEvent(event, arguments)
            if event.startswith("socket.") or event == "ctypes.dlopen":
                raise PermissionError(f"local kernel construction attempted {event}")

    sys.addaudithook(guard)
    try:
        results = {name: measure_case(name, case) for name, case in CASES.items()}
        require(len({len(raw) for raw, _, _ in results.values()}) == len(results)
                and len({len(frame) for _, frame, _ in results.values()}) == len(results),
                "bare BODY lengths do not vary across the neutral cases")
    finally:
        enabled = False
    return results, len(audit.DeniedReads)


def main():
    parser = argparse.ArgumentParser(description="Build and measure two independent bare BODY transmit candidates")
    parser.add_argument("--artifacts", type=Path, help="unused destination outside the repository")
    arguments = parser.parse_args()
    repository = Path(__file__).resolve().parents[4]
    destination = arguments.artifacts.resolve() if arguments.artifacts is not None else None
    if destination is not None:
        require(not destination.is_relative_to(repository) and not destination.exists(), "choose an unused external destination")
    results, denied = build_batch()
    if destination is not None:
        destination.mkdir()
        for name, (raw, wrapper, _) in results.items():
            (destination / (name + ".x_b")).write_bytes(raw)
            (destination / (name + ".frame")).write_bytes(wrapper)
    owning = (
        "re/tooling/sw2026/imported_body_source/BuildLocalBodyKernel.py",
        "re/tooling/sw2026/imported_body_source/LocalBodyKernel.py",
        "re/tooling/sw2026/para/rectangle/Geometry.py",
        "re/tooling/sw2026/para/rectangle/RectanglePartition.py",
        "src/convert/Geometry/Extrude/Polygon/PolygonExtrude.py",
        "tests/Convert/Solidworks/Research/ConstructionGuard.py",
    )
    print(json.dumps({
        "schema": "kit.sw2026.generated-local-body-kernel.v1",
        "externally_supplied_model_inputs": 0,
        "construction_denied_io_events": denied, "construction_source_file_reads": 0,
        "kernel_artifacts": len(results), "native_solidworks_outputs": 0, "native_acceptance": False,
        "cases": {name: measurement for name, (_, _, measurement) in results.items()},
        "owning_sources_sha256": {name: sha256((repository / name).read_bytes()).hexdigest() for name in owning},
        "runtime": {"python": platform.python_version(), "zlib": zlib.ZLIB_RUNTIME_VERSION},
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
