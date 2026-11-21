from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
import hashlib
import json
import math
import re

from convert.Geometry.Formula.Arithmetic import (
    EvalFormula,
    IsLiteralExpr,
    IsMatchingQty,
    ReadFormula,
)
from interchange import (
    LineCurve,
    LineGeometry,
    Parameter,
    ParameterValue,
    PlaneSurface,
    ValueKind,
)

QUALIFIED = re.compile(r"[A-Za-z_][A-Za-z_0-9]*(?:\.[A-Za-z_][A-Za-z_0-9]*)+")
TOLERANCE_MM = 1e-9


def require(value, message):
    if not value:
        raise ValueError(message)


def plain(value):
    if isinstance(value, Enum):
        return value.value
    if value is None or type(value) in (str, int, float, bool):
        return value
    if isinstance(value, bytes):
        return {
            "bytes": len(value),
            "sha256": hashlib.sha256(value).hexdigest(),
            "payload_excluded_from_projection": True,
        }
    if is_dataclass(value):
        return {
            field.name: plain(getattr(value, field.name)) for field in fields(value)
        }
    if isinstance(value, Mapping):
        return {str(key): plain(item) for key, item in value.items()}
    if isinstance(value, (set, frozenset)):
        return sorted(
            (plain(item) for item in value),
            key=lambda item: json.dumps(item, sort_keys=True),
        )
    if isinstance(value, (tuple, list)):
        return [plain(item) for item in value]
    raise TypeError("unclassified source value " + type(value).__name__)


def canonical(value):
    return (
        json.dumps(plain(value), sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n"
    ).encode()


def value_quantity(value):
    formula = ReadFormula(str(value.value) + (" " + value.unit if value.unit else ""))
    require(
        formula is not None and IsLiteralExpr(formula),
        "source arithmetic requires an actual literal numeric quantity",
    )
    result = EvalFormula(formula, {})
    require(
        result is not None, "source quantity has no checked canonical interpretation"
    )
    return result


@dataclass(frozen=True)
class DependencyPlan:
    nodes: tuple[dict, ...]
    expressions: tuple[dict, ...]
    evaluation_order: tuple[str, ...]
    typed_dependency_bindings_complete: bool


@dataclass(frozen=True)
class PartDrivers:
    body_id: str
    body_name: str
    sketch_id: str
    sketch_name: str
    feature_id: str
    feature_name: str
    support_plane_id: str
    width: Parameter
    height: Parameter
    depth: Parameter
    source_values_mm: tuple[float, float, float]
    native_values_m: tuple[float, float, float]
    native_generation_eligible: bool = False


def factory_drivers(document):
    sketch, feature, body, plane = source_profile(document)
    parameters = {value.id: value for value in document.parameters}
    result = []
    for entity in sketch.entities[:2]:
        candidates = [
            rule
            for rule in sketch.constraints
            if rule.kind == "distance"
            and rule.parameter_id
            and len(rule.references) == 1
            and rule.references[0].entity_id == entity.id
            and not rule.references[0].point
        ]
        require(
            len(candidates) == 1,
            "a factory driver has no unique actual source line-length constraint",
        )
        rule = candidates[0]
        raw = rule.attributes.get("freecad", {})
        require(
            raw.get("Type") == "6"
            and raw.get("FirstPos") == "0"
            and raw.get("Second") == "-2000"
            and raw.get("SecondPos") == "0"
            and raw.get("Third") == "-2000",
            "the source driver is not the independently bound one-line distance grammar",
        )
        parameter = parameters.get(rule.parameter_id)
        require(
            parameter is not None
            and parameter.owner_id == sketch.id
            and parameter.id in sketch.parameter_ids,
            "line length selects a foreign parameter owner",
        )
        length = math.hypot(
            entity.geometry.end.x - entity.geometry.start.x,
            entity.geometry.end.y - entity.geometry.start.y,
        )
        require(
            IsMatchingQty((length, (1, 0)), parameter.value),
            "the actual line length differs from its source dimension",
        )
        result.append(parameter)
    depth = [
        parameters[identity]
        for identity in feature.parameter_ids
        if identity in parameters
        and parameters[identity].attributes.get("freecad_path") == "Length"
    ]
    require(
        len(depth) == 1
        and depth[0].owner_id == feature.id
        and depth[0].value == feature.definition.length,
        "active Pad depth has no unique actual parameter owner",
    )
    result.append(depth[0])
    values = tuple(value_quantity(parameter.value)[0] for parameter in result)
    return PartDrivers(
        body.id,
        body.name,
        sketch.id,
        sketch.name,
        feature.id,
        feature.name,
        plane.id,
        *result,
        values,
        tuple(value / 1000 for value in values),
    )


def source_objects(document):
    require(
        document.source.format_id == "freecad.fcstd",
        "this source projection requires an actual FCStd neutral read",
    )
    objects = document.metadata.get("freecad", {}).get("objects")
    require(
        isinstance(objects, (list, tuple)) and objects,
        "actual FreeCAD object owners are absent",
    )
    result = {}
    for obj in objects:
        require(
            isinstance(obj, Mapping) and obj.get("name") not in result,
            "actual object names are missing or ambiguous",
        )
        result[obj["name"]] = obj
    for owner in (*document.sketches, *document.feature_timeline, *document.bodies):
        obj = owner.attributes.get("freecad")
        require(
            isinstance(obj, Mapping)
            and obj.get("name") in result
            and obj == result[obj["name"]],
            "a typed owner is stale against its actual native object",
        )
    return result


def dependency_plan(document):
    objects = source_objects(document)
    parameters = {value.id: value for value in document.parameters}
    require(
        len(parameters) == len(document.parameters),
        "source parameter IDs are ambiguous",
    )
    nodes = {}
    bindings = {}
    owner_names = {}
    source_paths = {}
    for sketch in document.sketches:
        obj = sketch.attributes["freecad"]
        for identity in sketch.parameter_ids:
            parameter = parameters.get(identity)
            require(
                parameter is not None and parameter.owner_id == sketch.id,
                "sketch driver has a stale actual owner",
            )
            index = re.fullmatch(
                r"Constraints\[([0-9]+)\]", parameter.attributes.get("freecad_path", "")
            )
            require(
                index is not None and int(index[1]) < len(sketch.constraints),
                "named source constraint has no actual ordered rule",
            )
            constraint = sketch.constraints[int(index[1])]
            raw = parameter.attributes.get("freecad_constraint")
            require(
                raw == constraint.attributes.get("freecad")
                and constraint.parameter_id == parameter.id,
                "constraint and parameter source ownership disagree",
            )
            name = raw.get("Name", "")
            require(name, "this projection requires an actual named source constraint")
            key = obj["name"] + ".Constraints." + name
            require(
                key not in bindings, "named source constraint reference is ambiguous"
            )
            bindings[key] = parameter.id
            owner_names[parameter.id] = obj["name"]
            source_paths[parameter.id] = (
                parameter.attributes["freecad_path"],
                "Constraints." + name,
            )
    for feature in document.feature_timeline:
        obj = feature.attributes["freecad"]
        for identity in feature.parameter_ids:
            parameter = parameters.get(identity)
            require(
                parameter is not None and parameter.owner_id == feature.id,
                "feature parameter has a stale actual owner",
            )
            path = parameter.attributes.get("freecad_path", "")
            require(
                path in obj["properties"]
                and parameter.attributes.get("freecad_property")
                == obj["properties"][path],
                "feature property and parameter source ownership disagree",
            )
            key = obj["name"] + "." + path
            require(key not in bindings, "feature-property reference is ambiguous")
            bindings[key] = parameter.id
            owner_names[parameter.id] = obj["name"]
            source_paths[parameter.id] = (path,)
    for parameter in document.parameters:
        nodes[parameter.id] = {
            "id": parameter.id,
            "kind": "parameter",
            "source_owner_id": parameter.owner_id,
            "source_name": parameter.name,
            "cached_value": plain(parameter.value),
            "parameter": parameter,
        }
    for obj in objects.values():
        if obj["type_id"] != "Spreadsheet::Sheet":
            continue
        owner = obj["properties"].get("cells", {})
        containers = [
            value for value in owner.get("children", ()) if value.get("tag") == "Cells"
        ]
        require(len(containers) == 1, "the actual sheet has no unique Cells owner")
        aliases = set()
        addresses = set()
        for cell in containers[0].get("children", ()):
            if cell.get("tag") != "Cell":
                continue
            attributes = cell.get("attributes", {})
            address = attributes.get("address", "")
            require(
                address and address not in addresses,
                "actual spreadsheet cell address is ambiguous",
            )
            addresses.add(address)
            alias = attributes.get("alias", "")
            if not alias:
                continue
            require(alias not in aliases, "actual spreadsheet alias is ambiguous")
            aliases.add(alias)
            key = obj["name"] + "." + alias
            require(
                key not in bindings,
                "spreadsheet alias collides with another actual owner",
            )
            content = attributes.get("content", "")
            require(
                content.startswith("="),
                "referenced source cell has no explicit formula owner",
            )
            formula = ReadFormula(content[1:])
            require(
                formula is not None and IsLiteralExpr(formula),
                "this source-cell member admits only a literal unit quantity",
            )
            quantity = EvalFormula(formula, {})
            require(
                quantity is not None and quantity[1] == (1, 0),
                "the actual alias is not a literal length quantity",
            )
            identity = "freecad:spreadsheet:" + obj["name"] + ":cell:" + address
            value = ParameterValue(quantity[0], ValueKind.LENGTH, "mm")
            nodes[identity] = {
                "id": identity,
                "kind": "spreadsheet_cell",
                "source_owner_name": obj["name"],
                "source_owner_object_id": obj["object_id"],
                "address": address,
                "alias": alias,
                "source_text": content,
                "cached_value": plain(value),
                "value": value,
                "native_target_owner_qualified": False,
            }
            bindings[key] = identity
    expressions = {}
    consumed = set()
    raw_expressions = {}
    for obj in objects.values():
        root = obj["properties"].get("ExpressionEngine", {})
        for container in root.get("children", ()):
            if container.get("tag") != "ExpressionEngine":
                continue
            rows = [
                row
                for row in container.get("children", ())
                if row.get("tag") == "Expression"
            ]
            require(
                int(container.get("attributes", {}).get("count", -1)) == len(rows),
                "the actual expression-engine count differs",
            )
            for row in rows:
                attributes = row.get("attributes", {})
                key = obj["name"], attributes.get("path", "").lstrip(".")
                require(
                    key[1] and key not in raw_expressions,
                    "actual expression path is empty or ambiguous",
                )
                raw_expressions[key] = attributes.get("expression", "")
    for parameter in document.parameters:
        require(
            parameter.id in owner_names and parameter.id in source_paths,
            "an actual source parameter has no bound property path",
        )
        matches = [
            (owner_names[parameter.id], path)
            for path in source_paths[parameter.id]
            if (owner_names[parameter.id], path) in raw_expressions
        ]
        require(
            len(matches) <= 1,
            "a source parameter is driven by ambiguous expression paths",
        )
        if parameter.expression is None:
            require(not matches, "the typed reader omitted a real source expression")
            continue
        expression = parameter.expression
        require(expression.language == "freecad", "unqualified expression language")
        require(
            len(matches) == 1 and raw_expressions[matches[0]] == expression.source,
            "the typed formula is stale against its actual expression-engine owner",
        )
        consumed.add(matches[0])
        aliases = {}
        linked = []

        def replace_name(match):
            text = match[0]
            require(
                text in bindings,
                "source expression references an absent or ambiguous actual owner",
            )
            identity = bindings[text]
            if identity not in linked:
                linked.append(identity)
            alias = "ref" + str(linked.index(identity))
            aliases[alias] = identity
            return alias

        translated = QUALIFIED.sub(replace_name, expression.source)
        formula = ReadFormula(translated)
        require(
            formula is not None and set(formula.Names) == set(aliases),
            "source formula is outside the explicit safe arithmetic grammar",
        )
        require(
            not expression.parameter_ids
            or tuple(expression.parameter_ids) == tuple(linked),
            "typed dependency IDs disagree with actual source owners",
        )
        expressions[parameter.id] = {
            "target_parameter_id": parameter.id,
            "source_text": expression.source,
            "original_parameter_ids": list(expression.parameter_ids),
            "resolved_owner_ids": linked,
            "safe_expression": translated,
            "aliases": aliases,
            "formula": formula,
            "target_cached_value": parameter.value,
        }
    require(
        consumed == set(raw_expressions),
        "an actual source expression has no represented parameter owner",
    )
    order = []
    visiting = set()
    values = {}

    def evaluate(identity):
        require(identity in nodes, "a source dependency node is missing")
        require(
            identity not in visiting,
            "the actual source dependency graph contains a cycle",
        )
        if identity in values:
            return values[identity]
        visiting.add(identity)
        node = nodes[identity]
        if identity in expressions:
            expression = expressions[identity]
            arguments = {
                alias: evaluate(owner) for alias, owner in expression["aliases"].items()
            }
            quantity = EvalFormula(expression["formula"], arguments)
            require(
                quantity is not None
                and IsMatchingQty(quantity, expression["target_cached_value"]),
                "cached source dimension is stale against its actual dependency graph",
            )
            value = expression["target_cached_value"]
            expression["evaluated_quantity"] = {
                "magnitude": quantity[0],
                "exponents": list(quantity[1]),
                "canonical_length_unit": "mm",
                "canonical_angle_unit": "rad",
            }
        else:
            value = node.get("value") or node["parameter"].value
        visiting.remove(identity)
        order.append(identity)
        values[identity] = value
        return value

    for identity in expressions:
        evaluate(identity)
    result_nodes = tuple(
        {key: value for key, value in row.items() if key not in ("parameter", "value")}
        for row in nodes.values()
    )
    result_expressions = tuple(
        {
            key: plain(value)
            for key, value in row.items()
            if key not in ("formula", "target_cached_value")
        }
        for row in expressions.values()
    )
    return DependencyPlan(
        result_nodes,
        result_expressions,
        tuple(order),
        all(bool(row["original_parameter_ids"]) for row in result_expressions),
    )


def point(value):
    return value.x, value.y, value.z


def close_point(left, right):
    return all(
        math.isfinite(value) and abs(value - wanted) <= TOLERANCE_MM
        for value, wanted in zip(left, right, strict=True)
    )


def topology_compare(source, generated, body_id):
    require(
        not source.validate(frozenset((body_id,)))
        and not generated.validate(frozenset((body_id,))),
        "source or generated analytic B-rep graph is invalid",
    )
    for model in (source, generated):
        require(
            (len(model.bodies), len(model.faces), len(model.edges), len(model.vertices))
            == (1, 6, 12, 8),
            "the measured rectangular boundary graph has changed",
        )
        require(
            all(type(curve) is LineCurve for curve in model.curves)
            and all(type(surface) is PlaneSurface for surface in model.surfaces),
            "rectangular source topology has nonplanar or curved owners",
        )
        indexed_vertices = {vertex.id: point(vertex.point) for vertex in model.vertices}
        indexed_curves = {curve.id: curve for curve in model.curves}
        for edge in model.edges:
            curve = indexed_curves[edge.curve_id]
            origin, direction = point(curve.origin), point(curve.direction)
            scale = math.sqrt(sum(value * value for value in direction))
            require(scale > 0, "rectangular line curve has a zero direction")
            for identity in (edge.start_vertex_id, edge.end_vertex_id):
                delta = tuple(
                    value - base
                    for value, base in zip(
                        indexed_vertices[identity], origin, strict=True
                    )
                )
                cross = (
                    delta[1] * direction[2] - delta[2] * direction[1],
                    delta[2] * direction[0] - delta[0] * direction[2],
                    delta[0] * direction[1] - delta[1] * direction[0],
                )
                require(
                    math.sqrt(sum(value * value for value in cross)) / scale
                    <= TOLERANCE_MM,
                    "rectangular edge endpoint is off its real line owner",
                )
    vertices = {}
    for vertex in source.vertices:
        matches = [
            candidate
            for candidate in generated.vertices
            if close_point(point(vertex.point), point(candidate.point))
        ]
        require(
            len(matches) == 1, "source B-rep vertex has no unique generated coordinate"
        )
        vertices[vertex.id] = matches[0].id
    require(
        len(set(vertices.values())) == len(vertices),
        "source vertex matching collapsed distinct topology",
    )
    by_ends = {
        tuple(sorted((edge.start_vertex_id, edge.end_vertex_id))): edge.id
        for edge in generated.edges
    }
    require(
        len(by_ends) == len(generated.edges),
        "generated rectangular edge endpoints are ambiguous",
    )
    edges = {}
    for edge in source.edges:
        key = tuple(
            sorted((vertices[edge.start_vertex_id], vertices[edge.end_vertex_id]))
        )
        require(
            key in by_ends and not edge.degenerate,
            "source edge has no actual generated endpoint pair",
        )
        edges[edge.id] = by_ends[key]
    require(
        len(set(edges.values())) == len(edges),
        "source edge matching collapsed distinct topology",
    )

    def face_edges(model, face):
        loops = {row.id: row for row in model.loops}
        coedges = {row.id: row for row in model.coedges}
        require(
            len(face.loop_ids) == 1, "the rectangular face has an unexpected inner loop"
        )
        loop = loops[face.loop_ids[0]]
        require(
            loop.outer and len(loop.coedge_ids) == 4,
            "the rectangular face does not have four outer coedges",
        )
        return tuple(sorted(coedges[key].edge_id for key in loop.coedge_ids))

    for model in (source, generated):
        indexed_vertices = {vertex.id: point(vertex.point) for vertex in model.vertices}
        indexed_edges = {edge.id: edge for edge in model.edges}
        indexed_surfaces = {surface.id: surface for surface in model.surfaces}
        for face in model.faces:
            surface = indexed_surfaces[face.surface_id]
            normal = point(surface.normal)
            scale = math.sqrt(sum(value * value for value in normal))
            require(scale > 0, "rectangular face has a zero surface normal")
            for edge_id in face_edges(model, face):
                edge = indexed_edges[edge_id]
                for identity in (edge.start_vertex_id, edge.end_vertex_id):
                    delta = tuple(
                        value - base
                        for value, base in zip(
                            indexed_vertices[identity],
                            point(surface.origin),
                            strict=True,
                        )
                    )
                    require(
                        abs(
                            sum(
                                value * axis
                                for value, axis in zip(delta, normal, strict=True)
                            )
                        )
                        / scale
                        <= TOLERANCE_MM,
                        "rectangular face vertex is off its actual surface",
                    )

    target_faces = {face_edges(generated, face): face.id for face in generated.faces}
    require(
        len(target_faces) == len(generated.faces),
        "generated face boundary ownership is ambiguous",
    )
    faces = {}
    for face in source.faces:
        key = tuple(sorted(edges[identity] for identity in face_edges(source, face)))
        require(
            key in target_faces,
            "source face has no exact generated edge-incidence boundary",
        )
        faces[face.id] = target_faces[key]
    require(
        len(set(faces.values())) == len(faces),
        "source face matching collapsed distinct topology",
    )
    return {
        "passed": True,
        "coordinate_tolerance_mm": TOLERANCE_MM,
        "vertices": len(vertices),
        "edges": len(edges),
        "faces": len(faces),
        "vertex_identity_map": vertices,
        "edge_identity_map": edges,
        "face_identity_map": faces,
        "measure_scope": "analytic rectangular boundary comparison, not a vendor mass evaluator",
    }


def rectangular_source_measure(source):
    values = [point(vertex.point) for vertex in source.vertices]
    lower = tuple(min(row[axis] for row in values) for axis in range(3))
    upper = tuple(max(row[axis] for row in values) for axis in range(3))
    require(
        len(set(values)) == 8
        and all(
            all(
                abs(row[axis] - bound) <= TOLERANCE_MM
                for axis, bound in enumerate(corner)
            )
            for row, corner in zip(
                sorted(values),
                sorted(
                    (x, y, z)
                    for x in (lower[0], upper[0])
                    for y in (lower[1], upper[1])
                    for z in (lower[2], upper[2])
                ),
                strict=True,
            )
        ),
        "source vertices do not form the declared axis-aligned rectangular boundary",
    )
    widths = tuple(high - low for low, high in zip(lower, upper, strict=True))
    require(
        all(value > 0 for value in widths),
        "source rectangular dimensions must be positive",
    )
    x, y, z = widths
    return {
        "bounds_mm": [list(lower), list(upper)],
        "volume_mm3": x * y * z,
        "area_mm2": 2 * (x * y + x * z + y * z),
        "center_mm": [(low + high) / 2 for low, high in zip(lower, upper, strict=True)],
        "method": "closed six-face rectangular boundary verified by the independent topology comparison",
    }


def source_profile(document):
    require(
        (
            len(document.sketches),
            len(document.feature_timeline),
            len(document.bodies),
            len(document.support_planes),
        )
        == (1, 1, 1, 3),
        "the source has owners outside the disclosed one-pad profile",
    )
    require(
        document.assembly is None
        and document.DrawingValue is None
        and not document.materials
        and not document.meshes,
        "additional source domains remain outside this projection",
    )
    sketch, feature, body = (
        document.sketches[0],
        document.feature_timeline[0],
        document.bodies[0],
    )
    require(
        len(sketch.entities) == 4
        and all(
            type(entity.geometry) is LineGeometry
            and not entity.construction
            and not entity.fixed
            for entity in sketch.entities
        ),
        "actual source geometry is not four ordinary unfixed lines",
    )
    require(
        len(sketch.closed_profile_entity_ids) == 1
        and tuple(entity.id for entity in sketch.entities)
        == sketch.closed_profile_entity_ids[0],
        "the source profile order differs from its actual entities",
    )
    require(
        feature.kind == "extrusion"
        and feature.sketch_id == sketch.id
        and not feature.suppressed,
        "source Pad does not bind its actual active sketch",
    )
    definition = feature.definition
    require(
        definition.end_condition == "blind"
        and not definition.reversed
        and not definition.symmetric
        and point(definition.direction) == (0, 0, 1),
        "source extrusion is outside the disclosed ordinary forward blind grammar",
    )
    (plane,) = [
        plane
        for plane in document.support_planes
        if plane.id == sketch.support_plane_id
    ]
    require(
        point(plane.transform.origin) == (0, 0, 0)
        and point(plane.transform.x_axis) == (1, 0, 0)
        and point(plane.transform.y_axis) == (0, 1, 0)
        and point(plane.transform.z_axis) == (0, 0, 1),
        "this source member needs the actual identity XY support frame",
    )
    return sketch, feature, body, plane


def constraint_owners(sketch):
    require(len(sketch.constraints) == 11, "the full source rule inventory has changed")
    records = []
    for rule in sketch.constraints:
        raw = rule.attributes.get("freecad")
        slots = rule.attributes.get("freecad_reference_slots")
        require(
            isinstance(raw, Mapping)
            and isinstance(slots, (list, tuple))
            and len(slots) == 3
            and rule.driving
            and not rule.suppressed,
            "source rule flags or native slots are missing",
        )
        rows = []
        for slot in slots:
            index, position = (
                slot["freecad_geometry_index"],
                slot["freecad_point_index"],
            )
            prefix = {"first": "First", "second": "Second", "third": "Third"}.get(
                slot["slot"]
            )
            require(
                prefix is not None
                and int(raw.get(prefix, -2000)) == index
                and int(raw.get(prefix + "Pos", 0)) == position,
                "typed source slot metadata is stale against the actual constraint",
            )
            if index >= 0:
                require(
                    index < len(sketch.entities)
                    and slot["entity_id"] == sketch.entities[index].id,
                    "rule slot selects another actual source entity",
                )
                rows.append(
                    {
                        "kind": "owned_sketch_entity",
                        "id": slot["entity_id"],
                        "point_code": position,
                    }
                )
            elif (index, position) == (-1, 1):
                rows.append(
                    {
                        "kind": "sketch_root_point",
                        "owner_sketch_id": sketch.id,
                        "support_plane_id": sketch.support_plane_id,
                        "source_geometry_id": -1,
                        "source_point_pos": 1,
                        "portable_reference_missing": True,
                        "public_source_rule": "FreeCAD 0.21.2 GeoEnum/GeoElementId::RtPnt",
                    }
                )
            else:
                require(
                    (index, position) == (-2000, 0),
                    "unqualified external source rule owner",
                )
        records.append(
            {
                "id": rule.id,
                "kind": rule.kind,
                "parameter_id": rule.parameter_id,
                "typed_reference_count": len(rule.references),
                "source_owners": rows,
                "raw_attributes_preserved": plain(rule.attributes),
            }
        )
    return records
