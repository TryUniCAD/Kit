from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from math import isclose, ulp

from OriginPortableGraph import require
from OriginPortableGeometry import one


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")


def tuple_value(items=()):
    return {"$tuple": list(items)}


def reference(entity_id, point=""):
    return {"$type": "ConstraintReference", "entity_id": entity_id, "point": point}


def relation(entity_id, kind, references, parameter=None):
    return {"$type": "SketchConstraint", "id": entity_id, "kind": kind, "references": tuple_value(references),
            "parameter_id": parameter, "driving": True, "suppressed": False, "attributes": {}, "provenance": None}


def length_value(metres):
    return {"$type": "ParameterValue", "kind": {"$enum": "ValueKind", "value": "length"}, "unit": "mm", "value": metres * 1000.}


def clean_record(value):
    return {**deepcopy(value), "attributes": {}, **({"provenance": None} if "provenance" in value else {})}


def neutral_child(case, geometry, boss, selected_plane, model_name):
    original = case["public_child_strict"]["document_wire"]
    source_sketch, = original["sketches"]["$tuple"]
    source_features = original["feature_timeline"]["$tuple"]
    source_boss = one([row for row in source_features if row["id"] == "sldprt:feature:" + str(boss["native_id"])], "public boss with the actual typed persistent identity")
    sketch_id, feature_id = source_sketch["id"], source_boss["id"]
    entities = []
    for index, point in enumerate(geometry["vertices_m"]):
        other = geometry["vertices_m"][(index + 1) % 4]
        entity_id = "native-profile:" + str(geometry["native_id"]) + ":line:" + str(geometry["line_roles"][index])
        entities.append({"$type": "SketchEntity", "id": entity_id, "kind": {"$enum": "GeometryKind", "value": "line"},
                         "geometry": {"$type": "LineGeometry", "start": {"$type": "Vector2", "x": point[0] * 1000., "y": point[1] * 1000.},
                                      "end": {"$type": "Vector2", "x": other[0] * 1000., "y": other[1] * 1000.}},
                         "construction": False, "fixed": False, "provenance": None, "attributes": {}})
    parameter_ids = ["native-profile:" + str(geometry["native_id"]) + ":length:" + driver["name"] for driver in geometry["drivers"]]
    depth_id = "native-feature:" + str(boss["native_id"]) + ":length:" + boss["depth_name"]
    parameters = [{"$type": "Parameter", "id": parameter_id, "name": name, "value": length_value(value), "owner_id": owner,
                   "expression": None, "role": {"$enum": "ParameterRole", "value": "driving"}, "attributes": {}, "provenance": None}
                  for parameter_id, name, value, owner in [*( (parameter_ids[index], driver["name"], driver["length_m"], sketch_id) for index, driver in enumerate(geometry["drivers"]) ),
                                                          (depth_id, boss["depth_name"], boss["depth_m"], feature_id)]]
    constraints = [relation(sketch_id + ":axis:" + str(index), "horizontal" if index % 2 == 0 else "vertical", [reference(entity["id"])])
                   for index, entity in enumerate(entities)]
    constraints.extend(relation(sketch_id + ":length:" + str(index), "distance", [reference(entities[index]["id"], "start"), reference(entities[index]["id"], "end")], parameter_ids[index]) for index in range(2))
    sketch = clean_record(source_sketch)
    sketch.update(name=geometry["sketch_name"], support_plane_id=selected_plane["id"], entities=tuple_value(entities), constraints=tuple_value(constraints),
                  parameter_ids=tuple_value(parameter_ids), closed_profile_entity_ids=tuple_value([tuple_value(entity["id"] for entity in entities)]), suppressed=False)
    feature = clean_record(source_boss)
    require(feature["definition"]["$type"] == "ExtrusionFeature" and not feature["suppressed"], "portable source public boss is absent or suppressed")
    require(feature["kind"] == {"$enum": "FeatureKind", "value": "extrusion"}
            and feature["operation"] in ({"$enum": "BooleanOperation", "value": "join"}, {"$enum": "BooleanOperation", "value": "create"})
            and feature["sketch_id"] == sketch_id
            and feature["input_feature_ids"]["$tuple"] in ([], ["sldprt:feature:" + str(geometry["native_id"])]),
            "portable source boss operation has another kind profile or prior feature input")
    feature["operation"] = {"$enum": "BooleanOperation", "value": "create"}
    feature.update(name=boss["name"], order=0, sketch_id=sketch_id, input_feature_ids=tuple_value(), parameter_ids=tuple_value([depth_id]), selection_ids=tuple_value(), configuration_states=tuple_value())
    feature["definition"]["length"] = length_value(boss["depth_m"])
    configurations = original["configurations"]["$tuple"]
    require(len(configurations) == 1 and configurations[0]["active"] and not configurations[0]["overrides"]["$tuple"] and not configurations[0]["suppressed_feature_ids"]["$tuple"],
            "portable source has another configuration or authored override")
    config = clean_record(configurations[0])
    body_values = original["bodies"]["$tuple"]
    require(len(body_values) == 1 and body_values[0]["material_id"] is None
            and body_values[0]["final_feature_id"] == feature_id
            and body_values[0]["topology"]["solid_count"] == 1,
            "portable source has another body material or final feature owner")
    body = clean_record(body_values[0]); body.update(name=boss["name"], final_feature_id=feature_id)
    result = deepcopy(original)
    result.update(configurations=tuple_value([config]), parameters=tuple_value(parameters), support_planes=tuple_value([clean_record(selected_plane)]),
                  sketches=tuple_value([sketch]), feature_timeline=tuple_value([feature]), bodies=tuple_value([body]),
                  metadata={"name": model_name}, diagnostics=tuple_value(), capabilities={"$frozenset": []})
    domains = project_domains(original, geometry, boss, source_boss)
    result["selections"] = tuple_value()
    return result, domains


def project_domains(original, geometry, boss, source_boss):
    for key in ("materials", "meshes", "brep_payloads"):
        require(not original[key]["$tuple"], "portable source contains an unsupported modeled domain: " + key)
    require(original["brep"] is None and original["assembly"] is None, "portable source has a native boundary or assembly domain")
    selections = original["selections"]["$tuple"]
    require(len(selections) <= 1, "portable source has additional selection semantics")
    projected = []
    for row in selections:
        require(row["$type"] == "Selection" and row["query"] == {
            "native_owner_id": boss["native_id"], "native_target_id": geometry["native_id"], "topology_role": "direction_axis"},
            "portable source selection does not describe the actual boss and profile normal")
        require(row["path"]["$tuple"] == [{"$type": "SelectionPathElement", "entity_id": geometry["sketch_name"],
                                               "entity_kind": "native", "subelement": "N_Axis"}],
                "portable source direction selection targets another actual normal owner")
        require(row["point"] is None and not row["attributes"]
                and row["name"] == boss["name"] + " direction N_Axis"
                and row["id"] == "sldprt:selection:" + str(boss["native_id"]) + ":axis:" + str(geometry["native_id"]) + ":N_Axis",
                "portable source direction selection has extra authored semantics")
        require(source_boss["definition"]["direction"] is None
                and all(row["id"] not in feature["selection_ids"]["$tuple"] for feature in original["feature_timeline"]["$tuple"]),
                "portable source direction selection is consumed as an explicit authored selection")
        projected.append({"selection_id": row["id"], "native_owner": boss["feature"], "native_profile": geometry["profile"],
                          "role": "implicit-profile-normal", "constructor_representation": "actual Front support and ordinary forward blind end without explicit direction",
                          "source_row_retained_in_inverse_ledger": True})
    return {"selection_projection": projected,
            "initial_body_operation": {"source_operation": source_boss["operation"], "constructor_operation": {"$enum": "BooleanOperation", "value": "create"},
                                       "actual_sole_boss": boss["feature"], "actual_profile": geometry["profile"],
                                       "rule": "the single first solid-producing boss owning the only final body creates that body; a join label with no predecessor is the reader projection, not a prior-body operand",
                                       "source_operation_retained_in_inverse_ledger": True},
            "materials": 0, "meshes": 0, "brep_payloads": 0,
            "native_boundary": False, "assembly": False}


def normalized_drawing(owners, geometry, boss):
    drawing = deepcopy(owners["drawing_wire"])
    sheet = drawing["sheets"]["$tuple"][0]; view = sheet["views"]["$tuple"][0]
    actual_sheet = owners["sheet_geometry"]
    require(sheet["scale_ratio"]["$tuple"] == actual_sheet["scale_ratio"], "portable source public and typed sheet scales differ")
    for key in ("width", "height"):
        actual, public = actual_sheet[key + "_m"], sheet[key]
        require(actual > 0. and abs(public - actual) <= max(ulp(public), ulp(actual)),
                "portable source public and actual typed paper sizes differ: " + key)
        sheet[key] = actual
    matrix = view["model_to_sheet"]
    if matrix is not None:
        require(matrix["$type"] == "Matrix4" and len(matrix["values"]["$tuple"]) == 16, "portable source view has an invalid typed affine transform")
        values = matrix["values"]["$tuple"]
        scale = view["scale_ratio"]["$tuple"][0] / view["scale_ratio"]["$tuple"][1]
        rotations = {"*Front": ((1., 0., 0.), (0., 1., 0.), (0., 0., 1.)), "*Top": ((1., 0., 0.), (0., 0., -1.), (0., 1., 0.)),
                     "*Right": ((0., 0., -1.), (0., 1., 0.), (1., 0., 0.))}
        require(view["orientation_name"] in rotations, "portable source has another named view family")
        rotation = rotations[view["orientation_name"]]
        xs, ys = zip(*geometry["vertices_m"], strict=True)
        center = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, boss["depth_m"] / 2)
        origin = (view["position"]["x"], view["position"]["y"], 0.)
        expected = [value for axis in range(3) for value in (*[scale * value for value in rotation[axis]], origin[axis] - scale * sum(a * b for a, b in zip(rotation[axis], center, strict=True)))] + [0., 0., 0., 1.]
        require(all(isclose(a, b, rel_tol=2e-7, abs_tol=1e-10) for a, b in zip(values, expected, strict=True)),
                "portable source view transform is not derived from its explicit orientation scale placement and current prism")
    outline = view["outline"]
    if outline is not None:
        require(matrix is not None and len(outline["$tuple"]) == 4, "portable source outline lacks its actual transform")
        xs, ys = zip(*geometry["vertices_m"], strict=True)
        points = [(x, y, z) for x in (min(xs), max(xs)) for y in (min(ys), max(ys)) for z in (0., boss["depth_m"])]
        projected = [[sum(values[axis * 4 + index] * point[index] for index in range(3)) + values[axis * 4 + 3] for axis in (0, 1)] for point in points]
        margin = min(sheet["width"], sheet["height"]) * .02
        expected = [min(p[0] for p in projected) - margin, min(p[1] for p in projected) - margin, max(p[0] for p in projected) + margin, max(p[1] for p in projected) + margin]
        require(all(isclose(a, b, rel_tol=2e-7, abs_tol=1e-10) for a, b in zip(outline["$tuple"], expected, strict=True)), "portable source outline has unrepresented displayed geometry or margins")
    view["model_to_sheet"] = None
    view["outline"] = None
    return drawing


def make_ledger(original, normalized):
    result = []
    for key in sorted(original.keys() | normalized.keys()):
        if key not in original or key not in normalized or original[key] != normalized[key]:
            result.append({"key": key, "had_source": key in original, "source": deepcopy(original.get(key)),
                           "normalized_sha256": sha256(canonical(normalized[key])).hexdigest() if key in normalized else None})
    return result


def restore(normalized, ledger):
    result = deepcopy(normalized)
    for item in ledger:
        key = item["key"]
        if item["normalized_sha256"] is None:
            require(key not in result, "inverse normalization unexpectedly acquired a removed field")
        else:
            require(key in result and sha256(canonical(result[key])).hexdigest() == item["normalized_sha256"], "inverse normalization input changed")
        if item["had_source"]:
            result[key] = deepcopy(item["source"])
        else:
            result.pop(key, None)
    return result
