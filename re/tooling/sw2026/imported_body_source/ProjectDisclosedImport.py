from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from itertools import combinations, product
from math import hypot, isfinite

import convert
from interchange import BrepModel, CadDocument, LineCurve, NativeFeatureDefinition, PlaneSurface, Transform
from interchange.brep.Validation.BrepValidate import GetBrepErrors

from BuildLocalBodyKernel import canonical_face, cross, difference, dot, prism_model
from LocalBodyKernel import require


FORMAT = "solidworks.sldprt"
RESOLVED_STREAM = "Contents/Config-0-ResolvedFeatures"
GEOMETRIC_RESIDUAL_MM = 1e-9
SYSTEM_FOLDERS = frozenset({
    "Comments", "Favorites", "History", "Selection Sets", "Sensors", "Design Binder",
    "Annotations", "Notes", "Surface Bodies", "Solid Bodies", "Markups", "Equations",
    "SOLIDWORKS Materials", "Lights and Cameras", "Ambient", "Directional", "Exploded Views",
})
STOCK_REFERENCES = {
    "Front Plane": "Plane", "Top Plane": "Plane", "Right Plane": "Plane", "Origin": "Sketch",
}
OMISSIONS = (
    "source part and body labels",
    "datum and system tree entries",
    "configuration identifiers, states and properties beyond the active configuration name",
    "material, appearance, document properties and application settings",
    "source entity identifiers, attributes and provenance",
    "source analytic carrier parameterization",
    "source archive structures, native payloads and tessellation",
)


@dataclass(frozen=True, slots=True)
class ImportedGeometry:
    model: BrepModel
    feature_name: str
    configuration_name: str
    body_name: str | None
    omissions: tuple[str, ...]
    omitted_capabilities: tuple[str, ...]
    omitted_metadata: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RectangularBoundary:
    limits: tuple[tuple[float, float], ...]
    vertices: frozenset
    edges: frozenset
    faces: frozenset


def decode_import(raw: bytes) -> CadDocument:
    require(type(raw) is bytes, "strict SDK decoding requires source bytes")
    return convert.open_document(
        raw, source_format=FORMAT, strict=True, include_brep=True, include_tessellation=False
    )


def feature_type(feature):
    definition = feature.definition
    return (
        definition.type_id
        if type(definition) is NativeFeatureDefinition
        and definition.format_id == FORMAT
        and feature.attributes.get("native_type") == definition.type_id
        else None
    )


def is_stock_feature(feature):
    kind = feature_type(feature)
    return (
        feature.kind == "native" and kind in SYSTEM_FOLDERS
        or feature.kind == "reference" and kind is not None and STOCK_REFERENCES.get(feature.name) == kind
    )


def active_configuration(document):
    require(len(document.configurations) == 1, "projection requires one configuration")
    config, = document.configurations
    require(config.active and config.name.strip() and config.parent_id is None
            and not config.overrides and not config.suppressed_feature_ids,
            "projection requires one active root configuration without overrides or suppression")
    manager = document.metadata.get("solidworks.typed_configuration_manager")
    require(isinstance(manager, Mapping) and manager.get("status") == "complete"
            and manager.get("configuration_count") == 1,
            "projection requires one decoded configuration manager record")
    records = manager.get("configurations")
    require(type(records) is tuple and len(records) == 1 and isinstance(records[0], Mapping),
            "projection requires one typed native configuration owner")
    record, = records
    require(record.get("native_class") == "moPartConfiguration_c"
            and record.get("name") == config.name
            and record.get("selected_by_f360") is True and record.get("selected_by_f368") is True
            and type(record.get("native_object_id")) is int
            and record.get("native_object_id") == config.attributes.get("native_object_id")
            and config.attributes.get("native_configuration_id") == 0,
            "active configuration name or identity lacks a matching selected native owner")
    return config


def source_owners(document):
    require(type(document) is CadDocument and document.source.format_id == FORMAT
            and document.schema_version == "1.0" and document.units == "mm"
            and document.assembly is None and document.DrawingValue is None,
            "projection requires a strict millimetre SOLIDWORKS part document")
    config = active_configuration(document)
    authored = tuple(feature for feature in document.feature_timeline if not is_stock_feature(feature))
    require(len(authored) == 1, "projection requires one authored native import feature")
    feature, = authored
    owner = feature.attributes.get("typed_archive_owner")
    require(feature.kind == "imported" and feature_type(feature) == "Imported"
            and isinstance(owner, Mapping) and owner.get("class") == "moBaseBody_c"
            and owner.get("stream") == RESOLVED_STREAM
            and owner.get("field_span") is False and feature.name.strip()
            and not (feature.suppressed or feature.configuration_states or feature.operation
                     or feature.sketch_id or feature.input_feature_ids or feature.parameter_ids or feature.selection_ids
                     or document.sketches or document.parameters or document.selections),
            "projection requires an unsuppressed native moBaseBody_c import without parametric inputs")
    decoded = feature.definition.object_data
    properties = decoded.get("properties")
    native_id = decoded.get("native_object_id")
    require(decoded.get("native_class") == "moBaseBody_c" and decoded.get("native_stream") == RESOLVED_STREAM
            and type(native_id) is int and native_id == feature.attributes.get("native_object_id")
            and isinstance(properties, Mapping) and properties.get("Name") == feature.name
            and properties.get("Type") == "Imported" and properties.get("id") == str(native_id),
            "import feature name or identity does not agree with its typed native owner")
    require(len(document.bodies) == 1 and document.bodies[0].final_feature_id == feature.id,
            "projection requires one design body owned by the native import")
    return feature, config, document.bodies[0]


def coordinates(vector):
    result = (vector.x, vector.y, vector.z)
    require(all(isfinite(value) for value in result), "nonfinite geometric coordinate")
    return result


def edge_key(left, right):
    return tuple(sorted((left, right)))


def rectangular_edges(model, points, expected):
    curves = {curve.id: curve for curve in model.curves}
    require({edge.curve_id for edge in model.edges} == set(curves)
            and all(type(curve) is LineCurve for curve in curves.values()),
            "projection requires one analytic line carrier per edge")
    edges = {}
    for edge in model.edges:
        left, right = points[edge.start_vertex_id], points[edge.end_vertex_id]
        require(edge_key(left, right) in expected, "source edge does not join adjacent box corners")
        line = curves[edge.curve_id]
        origin, direction = coordinates(line.origin), coordinates(line.direction)
        axis, = (index for index in range(3) if left[index] != right[index])
        require(all(abs(value) == int(index == axis) for index, value in enumerate(direction)),
                "edge line direction is not a unit vector along its box axis")
        require(edge.start_parameter != edge.end_parameter, "edge trim has identical parameters")
        for parameter, point in ((edge.start_parameter, left), (edge.end_parameter, right)):
            require(isfinite(parameter), "nonfinite edge trim parameter")
            actual = tuple(base + parameter * step for base, step in zip(origin, direction, strict=True))
            require(hypot(*difference(actual, point)) <= GEOMETRIC_RESIDUAL_MM,
                    "edge line trim does not reach its source vertex")
        edges[edge.id] = (left, right)
    require(frozenset(edge_key(*edge) for edge in edges.values()) == expected,
            "source box edges are duplicated or incomplete")
    return edges


def rectangular_faces(model, limits, points, edges):
    surfaces = {surface.id: surface for surface in model.surfaces}
    loops = {loop.id: loop for loop in model.loops}
    coedges = {coedge.id: coedge for coedge in model.coedges}
    require({face.surface_id for face in model.faces} == set(surfaces)
            and all(type(surface) is PlaneSurface for surface in surfaces.values()),
            "projection requires one analytic plane carrier per face")
    require(all(face.same_sense and len(face.loop_ids) == 1 for face in model.faces)
            and {face.loop_ids[0] for face in model.faces} == set(loops),
            "source planes require one outward face and one outer trim each")
    sides, rings, uses, directions = set(), set(), Counter(), Counter()
    for face in model.faces:
        loop = loops[face.loop_ids[0]]
        require(loop.outer and len(loop.coedge_ids) == 4, "a box face requires four outer coedges")
        boundary = []
        for identifier in loop.coedge_ids:
            coedge = coedges[identifier]
            require(not coedge.pcurve_id, "a source coedge includes an extra surface trim")
            start, end = edges[coedge.edge_id]
            boundary.append((end, start) if coedge.reversed else (start, end))
            uses[identifier] += 1
            directions[coedge.edge_id, coedge.reversed] += 1
        require(all(left[1] == right[0] for left, right in zip(boundary, boundary[1:] + boundary[:1], strict=True)),
                "source face trim does not form a consecutive closed loop")
        ring = tuple(start for start, end in boundary)
        require(len(set(ring)) == 4, "source face trim repeats a vertex")
        planar_axes = tuple(index for index in range(3) if len({point[index] for point in ring}) == 1)
        require(len(planar_axes) == 1, "source face does not occupy a unique box side")
        axis, = planar_axes
        level = ring[0][axis]
        require(set(ring) == {point for point in points.values() if point[axis] == level},
                "source face trim does not bound all four corners of its box side")
        outward = -1 if level == limits[axis][0] else 1
        plane = surfaces[face.surface_id]
        normal, origin, reference = coordinates(plane.normal), coordinates(plane.origin), coordinates(plane.reference_direction)
        require(normal == tuple(outward if index == axis else 0 for index in range(3))
                and abs(origin[axis] - level) <= GEOMETRIC_RESIDUAL_MM,
                "source face plane does not coincide with its outward box side")
        require(abs(hypot(*reference) - 1) <= 1e-12 and abs(dot(reference, normal)) <= 1e-12,
                "source plane reference direction is not orthonormal")
        require(dot(cross(difference(ring[1], ring[0]), difference(ring[2], ring[1])), normal) > 0,
                "source face trim winding opposes its plane")
        sides.add((axis, level))
        rings.add(canonical_face(ring))
    require(sides == {(axis, level) for axis, pair in enumerate(limits) for level in pair},
            "source must have one planar face per box side")
    require(uses == Counter(coedges.keys())
            and directions == Counter((identifier, reversed_use) for identifier in edges for reversed_use in (False, True)),
            "source closed shell must have exactly two opposite face trims per edge")
    return frozenset(rings)


def rectangular_boundary(model, design_body_id=""):
    require(type(model) is BrepModel and model.schema_version == "1.0",
            "projection requires a typed SDK B-rep")
    errors = GetBrepErrors(model, frozenset({design_body_id}) if design_body_id else frozenset())
    require(not errors, "invalid source B-rep: " + "; ".join(errors))
    counts = tuple(len(getattr(model, name)) for name in (
        "bodies", "regions", "shells", "shell_uses", "faces", "face_uses", "loops",
        "coedges", "edges", "vertices", "curves", "surfaces",
    ))
    require(counts == (1, 1, 1, 1, 6, 6, 6, 24, 12, 8, 12, 6)
            and not (model.wires or model.pcurves),
            "projection requires a six-face rectangular solid with no loose geometry")
    body, region, shell, shell_use = model.bodies[0], model.regions[0], model.shells[0], model.shell_uses[0]
    require(body.transform == Transform() and body.design_body_id in ("", design_body_id)
            and body.region_ids == (region.id,) and not (body.wire_ids or body.vertex_ids)
            and region.solid and region.shell_use_ids == (shell_use.id,)
            and shell_use.shell_id == shell.id and not shell_use.reversed and shell.closed
            and set(shell.face_use_ids) == {use.id for use in model.face_uses}
            and {use.face_id for use in model.face_uses} == {face.id for face in model.faces}
            and not any(use.reversed for use in model.face_uses),
            "source body does not have one outward closed solid shell")
    require(not any(item.tolerance for item in (*model.vertices, *model.edges, *model.faces))
            and not any(edge.degenerate for edge in model.edges),
            "source solid has degenerate topology or local tolerances")
    points = {vertex.id: coordinates(vertex.point) for vertex in model.vertices}
    corners = frozenset(points.values())
    limits = tuple(tuple(sorted({point[index] for point in corners})) for index in range(3))
    require(all(len(axis) == 2 for axis in limits) and len(corners) == 8
            and corners == frozenset(product(*limits)),
            "source vertices do not describe all eight distinct axis-aligned box corners")
    expected_edges = frozenset(
        edge_key(left, right) for left, right in combinations(corners, 2)
        if sum(a != b for a, b in zip(left, right, strict=True)) == 1
    )
    edges = rectangular_edges(model, points, expected_edges)
    faces = rectangular_faces(model, limits, points, edges)
    return RectangularBoundary(limits, corners, expected_edges, faces)


def project_import(document: CadDocument) -> ImportedGeometry:
    feature, configuration, body = source_owners(document)
    boundary = rectangular_boundary(document.brep, body.id)
    (left, right), (front, back), elevation = boundary.limits
    section = ((left, front), (right, front), (right, back), (left, back))
    model = prism_model("imported-geometry", section, elevation)
    require(rectangular_boundary(model) == boundary, "generated neutral topology disagrees with source topology")
    return ImportedGeometry(
        model, feature.name, configuration.name, None, OMISSIONS,
        tuple(sorted(capability.value for capability in document.capabilities if capability.value != "brep")),
        tuple(sorted(document.metadata)),
    )
