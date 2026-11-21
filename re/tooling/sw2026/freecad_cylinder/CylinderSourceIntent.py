from hashlib import sha256
import json
from math import isfinite, pi

from convert.Geometry.Extrude.Circular.CircularExtrude import BuildCircular
from interchange.document.Models.DocumentModel import CadDocument
from interchange.document.Validation.DocumentValidate import AssertValid
from interchange.Features.FeatureKinds import NativeFeature
from interchange.geometry.Models.GeometryCurves import CircleGeometry
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.serialization.EncodeData import ToData

from CorrelateCylinderBrep import correlate


def require(value, reason):
    if not value:
        raise ValueError(reason)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def fingerprint(value):
    return sha256(canonical(value)).hexdigest()


def field_value(properties, name, field_type, child_tag):
    require(name in properties, f"missing source property {name}")
    field = properties[name]
    require(field["tag"] == "Property" and field["attributes"]["name"] == name
            and field["attributes"]["type"] == field_type,
            f"source property type differs: {name}")
    children = field.get("children", [])
    require(len(children) == 1 and children[0]["tag"] == child_tag,
            f"source property framing differs: {name}")
    return children[0]["attributes"]


def scalar_value(field):
    kind = field["attributes"]["type"]
    children = field.get("children", [])
    require(children, "source scalar property has no value")
    child = children[0]
    attributes = child["attributes"]
    if kind in ("App::PropertyLength", "App::PropertyAngle", "App::PropertyFloat"):
        require(len(children) == 1 and child["tag"] == "Float", "source float property framing differs")
        value = float(attributes["value"])
        require(isfinite(value), "source scalar property is nonfinite")
        return value, {"App::PropertyLength": ("length", "mm"),
                       "App::PropertyAngle": ("angle", "deg"),
                       "App::PropertyFloat": ("number", "")}[kind]
    if kind == "App::PropertyString":
        require(len(children) == 1 and child["tag"] == "String", "source text property framing differs")
        return attributes["value"], ("string", "")
    if kind == "App::PropertyBool":
        require(len(children) == 1 and child["tag"] == "Bool"
                and attributes["value"] in ("true", "false"), "source boolean property framing differs")
        return attributes["value"] == "true", ("boolean", "")
    require(kind == "App::PropertyEnumeration" and child["tag"] == "Integer",
            "source scalar property is outside the declared primitive vocabulary")
    index = int(attributes["value"])
    if len(children) == 1:
        require(attributes.get("CustomEnum") != "true", "source enum is missing its actual labels")
        return index, ("integer", "")
    require(len(children) == 2 and attributes.get("CustomEnum") == "true"
            and children[1]["tag"] == "CustomEnumList", "source custom enum framing differs")
    entries = children[1].get("children", [])
    require(int(children[1]["attributes"]["count"]) == len(entries)
            and 0 <= index < len(entries) and all(item["tag"] == "Enum" for item in entries),
            "source enum selector is outside its owned labels")
    return entries[index]["attributes"]["value"], ("string", "")


def identity_placement(properties, name):
    values = field_value(properties, name, "App::PropertyPlacement", "PropertyPlacement")
    require(set(values) == {"A", "Ox", "Oy", "Oz", "Px", "Py", "Pz", "Q0", "Q1", "Q2", "Q3"},
            f"source placement fields differ: {name}")
    require(all(isfinite(float(value)) for value in values.values()), f"source placement is nonfinite: {name}")
    position = tuple(float(values[key]) for key in ("Px", "Py", "Pz"))
    quaternion = tuple(float(values[key]) for key in ("Q0", "Q1", "Q2", "Q3"))
    require(position == (0.0, 0.0, 0.0) and quaternion == (0.0, 0.0, 0.0, 1.0)
            and float(values["A"]) == 0.0, f"source {name} is outside the origin-aligned profile")
    return {"position_mm": list(position), "quaternion_xyzw": list(quaternion),
            "axis_angle_degrees": {key: float(values[key]) for key in ("A", "Ox", "Oy", "Oz")}}


def measure(radius_mm, depth_mm, body_id):
    require(type(radius_mm) in (int, float) and type(depth_mm) in (int, float)
            and isfinite(radius_mm) and isfinite(depth_mm) and radius_mm > 0 and depth_mm > 0,
            "cylinder prediction requires finite positive independent drivers")
    volume = pi * radius_mm * radius_mm * depth_mm
    area = 2 * pi * radius_mm * (radius_mm + depth_mm)
    model, shared_volume, shared_area, bounds = BuildCircular(
        body_id, Transform(), CircleGeometry(PlaneVector(0.0, 0.0), radius_mm),
        0.0, depth_mm, radius_mm, radius_mm,
    )
    return {
        "radius_mm": radius_mm, "depth_mm": depth_mm, "bodies": 1,
        "volume_mm3": volume, "area_mm2": area, "center_mm": [0.0, 0.0, depth_mm / 2],
        "bounds_mm": [[-radius_mm, -radius_mm, 0.0], [radius_mm, radius_mm, depth_mm]],
        "shared_geometry": {"volume_mm3": shared_volume, "area_mm2": shared_area,
                            "bounds": ToData(bounds), "faces": len(model.faces),
                            "body_ids": [body.id for body in model.bodies],
                            "model_sha256": fingerprint(ToData(model))},
        "frame_kind": "derived_analysis_frame_not_an_authored_support",
    }


def project(document):
    require(type(document) is CadDocument, "source intent requires the concrete strict portable document")
    AssertValid(document)
    require(document.schema_version == "1.0" and str(document.units) == "mm"
            and not document.diagnostics, "source document schema units or diagnostics are unsupported")
    require(document.source.format_id == "freecad.fcstd" and document.source.sha256
            and dict(document.source.attributes) == {"freecad_schema_version": "4"},
            "source intent requires the actual schema-four FreeCAD source identity")
    require(len(document.feature_timeline) == len(document.bodies) == len(document.configurations) == 1,
            "source intent requires one actual primitive body and configuration")
    require(not document.sketches and not document.support_planes and not document.selections
            and not document.meshes and not document.materials
            and document.assembly is None and document.DrawingValue is None,
            "source intent has unsupported additional portable owners")
    feature, body, config = document.feature_timeline[0], document.bodies[0], document.configurations[0]
    require(str(feature.kind) == "primitive" and type(feature.definition) is NativeFeature
            and feature.definition.format_id == "freecad.fcstd" and feature.definition.type_id == "Part::Cylinder",
            "source intent requires the actual Part::Cylinder native feature owner")
    require(not feature.suppressed and feature.order == 0 and not feature.input_feature_ids
            and not feature.selection_ids and feature.sketch_id is None and feature.operation is None
            and not feature.configuration_states, "source primitive has unsupported history or optional state")
    require(body.final_feature_id == feature.id and body.material_id is None,
            "source body does not resolve the primitive or has a portable material owner")
    require(config.active and config.parent_id is None and not config.overrides
            and not config.suppressed_feature_ids and not config.attributes,
            "source configuration has unrepresented state")
    source = ToData(document)
    native = source["feature_timeline"]["$tuple"][0]["definition"]["object_data"]
    metadata = source["metadata"]
    require(set(metadata) == {"freecad"}, "source metadata has foreign owners")
    freecad = metadata["freecad"]
    require(freecad.get("schema_version") == "4" and freecad.get("objects") == [native]
            and source["feature_timeline"]["$tuple"][0]["attributes"].get("freecad") == native,
            "source native object copies disagree or were stripped")
    require(native["type_id"] == "Part::Cylinder" and native["order"] == 0
            and native["dependencies"] == [] and native["touched"] is False,
            "source primitive native type or dependency state differs")
    require(feature.id == f"freecad:feature:{native['name']}" and body.id == "freecad:body:default"
            and body.name == "Body" and dict(body.attributes) == {"freecad_generated": True},
            "source primitive or synthesized default body identity differs from its strict reader owner")
    require(feature.provenance is not None and feature.provenance.adapter == "freecad.fcstd"
            and feature.provenance.native_id == native["name"] and not feature.provenance.spans,
            "source feature provenance no longer identifies its native object")
    properties = native["properties"]
    order = native["property_order"]
    require(set(properties) == {"Angle", "AttacherEngine", "AttacherType", "AttachmentOffset",
                               "AttachmentSupport", "ExpressionEngine", "FirstAngle", "Height", "Label",
                               "Label2", "MapMode", "MapPathParameter", "MapReversed", "Placement", "Radius",
                               "SecondAngle", "Shape", "ShapeMaterial", "Visibility"},
            "source primitive has an unclassified property owner")
    require(len(order) == len(set(order)) and set(order) == set(properties),
            "source property order is duplicated or incomplete")
    require([parameter.id for parameter in document.parameters] == list(feature.parameter_ids),
            "source parameter order is not the actual feature order")
    by_path, parameter_rows = {}, []
    for parameter in document.parameters:
        attributes = ToData(parameter)["attributes"]
        path = attributes.get("freecad_path")
        require(isinstance(path, str) and path in properties and path not in by_path,
                "source parameter path is missing duplicated or foreign")
        require(parameter.owner_id == feature.id and str(parameter.role) == "driving"
                and parameter.expression is None, f"source parameter lost its driving owner: {path}")
        require(parameter.id == f"freecad:parameter:{native['name']}:{path}"
                and parameter.name == feature.name + "." + path,
                f"source parameter identity or name differs from its actual primitive owner: {path}")
        require(attributes.get("freecad_property") == properties[path]
                and attributes.get("freecad_property_type") == properties[path]["attributes"]["type"],
                f"source parameter property owner is stale: {path}")
        expected, (kind, unit) = scalar_value(properties[path])
        require(parameter.value.value == expected and type(parameter.value.value) is type(expected)
                and str(parameter.value.kind) == kind and parameter.value.unit == unit,
                f"source parameter value differs from its native property: {path}")
        by_path[path] = parameter
        parameter_rows.append({"id": parameter.id, "name": parameter.name, "owner_id": parameter.owner_id,
                               "path": path, "role": str(parameter.role), "kind": kind, "unit": unit,
                               "value": parameter.value.value,
                               "native_property_sha256": fingerprint(properties[path]),
                               "native_mapping": "geometry_input" if path in ("Radius", "Height") else "unrepresented"})
    scalar_types = {"App::PropertyLength", "App::PropertyAngle", "App::PropertyFloat",
                    "App::PropertyString", "App::PropertyBool", "App::PropertyEnumeration"}
    require([name for name in order if properties[name]["attributes"]["type"] in scalar_types] == list(by_path),
            "source scalar parameters were stripped or reordered")
    radius, height = by_path["Radius"].value.value, by_path["Height"].value.value
    require(by_path["Angle"].value.value == 360.0 and by_path["FirstAngle"].value.value == 0.0
            and by_path["SecondAngle"].value.value == 0.0, "source cylinder is outside the declared full-sweep profile")
    label = field_value(properties, "Label", "App::PropertyString", "String")["value"]
    require(feature.name == label, "source feature name differs from its actual label")
    placement = identity_placement(properties, "Placement")
    offset = identity_placement(properties, "AttachmentOffset")
    for name, kind, tag in (("AttachmentSupport", "App::PropertyLinkSubList", "LinkSubList"),
                            ("ExpressionEngine", "App::PropertyExpressionEngine", "ExpressionEngine")):
        require(field_value(properties, name, kind, tag) == {"count": "0"},
                f"source cylinder has unsupported {name}")
    require(by_path["MapMode"].value.value == 0 and by_path["MapPathParameter"].value.value == 0.0
            and by_path["MapReversed"].value.value is False, "source cylinder has active attachment mapping")
    document_properties = freecad["document_properties"]["children"]
    labels = [field for field in document_properties if field["attributes"]["name"] == "Label"]
    require(len(labels) == 1 and labels[0]["attributes"]["type"] == "App::PropertyString",
            "source document label is absent or ambiguous")
    name = labels[0]["children"][0]["attributes"]["value"]
    require(isinstance(name, str) and bool(name) and bool(feature.name) and bool(body.name),
            "source document feature and body names must remain explicit")
    payloads = []
    for value in document.brep_payloads:
        require(value.data is not None and sha256(value.data).hexdigest() == value.sha256,
                "source payload identity is stale")
        payloads.append({"id": value.id, "kind": value.kind, "format_id": value.format_id,
                         "sha256": value.sha256, "bytes": len(value.data), "role": str(value.role),
                         "construction_use": "excluded"})
    expected_kinds = {"native_document", "native_document_binding"} | ({"shape"} if document.brep is not None else set())
    require(len(payloads) == len(expected_kinds) and {row["kind"] for row in payloads} == expected_kinds
            and next(row["sha256"] for row in payloads if row["kind"] == "native_document") == document.source.sha256,
            "source document payload binding is absent or differs")
    if document.brep is not None:
        shape = next(value for value in document.brep_payloads if value.kind == "shape")
        require(shape.attributes.get("feature_id") == feature.id
                and shape.attributes.get("freecad_object") == native["name"]
                and shape.attributes.get("freecad_property") == "Shape"
                and shape.attributes.get("freecad.native_document_sha256") == document.source.sha256,
                "source B-rep payload is not owned by the actual primitive")
    shape_material = field_value(properties, "ShapeMaterial", "Materials::PropertyMaterial", "PropertyMaterial")
    unmapped = [row["path"] for row in parameter_rows if row["native_mapping"] == "unrepresented"]
    result = {
        "schema": "kit.sw2026.freecad-cylinder-source-intent.v1", "source_geometry_projected": True,
        "native_construction_admitted": False, "source_equivalence_qualified": False,
        "source_sha256": document.source.sha256, "full_document_sha256": fingerprint(source),
        "projection_variant": "current_with_owned_brep" if document.brep is not None else "historical_without_portable_brep",
        "native_object_sha256": fingerprint(native),
        "names": {"document": name, "feature": feature.name, "body": body.name, "configuration": config.name},
        "body_identity_origin": "strict_reader_synthesized_default_body_not_an_authored_container",
        "identities": {"feature": feature.id, "body": body.id, "configuration": config.id,
                       "radius_parameter": by_path["Radius"].id, "height_parameter": by_path["Height"].id,
                       "native_object": native["name"]},
        "parameter_order": list(feature.parameter_ids), "parameters": parameter_rows,
        "placement": placement, "attachment_offset": offset,
        "explicit_absences": {"authored_sketch": True, "authored_support_datum": True,
                              "authored_boolean_operation": True, "portable_brep": document.brep is None,
                              "portable_material": True, "assembly": True, "drawing": True,
                              "expressions": True, "attachment_support": True, "configuration_overrides": True},
        "retained_envelope": {"metadata_sha256": fingerprint(metadata),
                              "feature_attributes_sha256": fingerprint(source["feature_timeline"]["$tuple"][0]["attributes"]),
                              "body_sha256": fingerprint(source["bodies"]["$tuple"][0]),
                              "document_property_names": [field["attributes"]["name"] for field in document_properties],
                              "native_property_order": order, "native_payloads": payloads,
                              "shape_material_reference_present": bool(shape_material.get("uuid")),
                              "shape_material_owner_sha256": fingerprint(properties["ShapeMaterial"])},
        "required_mapping": {"radius": {"source_parameter_id": by_path["Radius"].id,
                                         "native_role": "radius_driven_circle", "units": "mm_to_m"},
                             "height": {"source_parameter_id": by_path["Height"].id,
                                        "native_role": "forward_blind_depth", "units": "mm_to_m"},
                             "feature_name": {"source": feature.name, "native_role": "boss_feature_name"},
                             "body_name": {"source": body.name, "native_role": "actual_live_body_name"}},
        "unrepresented_parameter_paths": unmapped,
        "blocked_native_owners": ["primitive_to_derived_sketch_support_history", "full_source_metadata_and_provenance",
                                  "native_shape_material_reference", "body_caption", "all_other_source_parameter_roles"],
        "predicted_pristine": measure(radius, height, body.id),
        "source_brep": correlate(document, radius, height, body.id),
        "generated_writer_outputs": 0, "native_processes_started": 0, "heldout_inputs_read": 0,
    }
    return result


def predict(intent, radius_factor, depth_factor):
    base = intent["predicted_pristine"]
    radius, height = base["radius_mm"], base["depth_mm"]
    require(all(type(value) in (int, float) and isfinite(value) and value > 0
                for value in (radius_factor, depth_factor)), "independent edit factors must be finite and positive")
    return {
        "schema": "kit.sw2026.freecad-cylinder-independent-prediction.v1",
        "source_sha256": intent["source_sha256"],
        "source_document_sha256": intent["full_document_sha256"],
        "source_driver_ids": {"Radius": intent["identities"]["radius_parameter"],
                              "Height": intent["identities"]["height_parameter"]},
        "pristine": base,
        "independent_radius_edit": measure(radius * radius_factor, height, intent["identities"]["body"]),
        "independent_depth_edit": measure(radius, height * depth_factor, intent["identities"]["body"]),
        "native_source_observations_read": False, "generated_writer_outputs": 0,
    }
