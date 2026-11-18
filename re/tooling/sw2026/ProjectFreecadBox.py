from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from itertools import product
from math import isclose, isfinite
from uuid import UUID

from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.PartTextInput import PartTextInput
from interchange import CadDocument, NativeFeatureDefinition
from interchange.document.Validation.DocumentValidate import AssertValid
from tests.Convert.Solidworks.Research.Construction.RectangleAnchors.MakeCornerDoc import MakeCornerDoc


FEATURE_PROPERTIES = {
    "AddSubShape", "AttacherType", "AttachmentOffset", "BaseFeature", "ExpressionEngine", "Height", "Label",
    "Label2", "Length", "MapMode", "MapPathParameter", "MapReversed", "Placement", "Refine", "Shape", "Support",
    "Visibility", "Width",
}
BODY_PROPERTIES = {"BaseFeature", "ExpressionEngine", "Group", "Label", "Label2", "Origin", "Placement", "Shape",
                   "Tip", "Visibility"}
DOCUMENT_PROPERTIES = {
    "FileName", "Tip", "TransientDir", "Comment", "Company", "CreatedBy", "CreationDate", "Id", "Label",
    "LastModifiedBy", "LastModifiedDate", "License", "LicenseURL", "Material", "Meta", "ShowHidden", "TipName", "Uid",
}
AXIS_ROLES = {"XY-plane": "Front Plane", "XZ-plane": "Top Plane", "YZ-plane": "Right Plane"}
PLANE_FRAMES = {
    "XY-plane": ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
    "XZ-plane": ((1, 0, 0), (0, 0, -1), (0, 1, 0)),
    "YZ-plane": ((0, 0, -1), (0, 1, 0), (1, 0, 0)),
}
DIMENSIONS = ("Length", "Width", "Height")


@dataclass(frozen=True, slots=True)
class BoxProjection:
    model: CadDocument
    properties: PartTextInput
    dimensions_mm: tuple[float, float, float]
    creation_epoch: int
    parameter_bindings: dict[str, str]
    source_body_label: str
    source_feature_label: str
    geometry: dict


def require(value, message):
    if not value:
        raise ValueError(message)


def child(prop, kind, tag):
    require(prop["tag"] == "Property" and prop["attributes"]["type"] == "App::Property" + kind,
            f"FreeCAD property has a different type for {prop['attributes']['name']}")
    values = prop["children"]
    require(len(values) == 1 and values[0]["tag"] == tag, "FreeCAD property shape differs from the documented object")
    return values[0]


def value(properties, name, kind, tag):
    return child(properties[name], kind, tag)["attributes"]["value"]


def default(properties, name, kind, tag, expected):
    require(value(properties, name, kind, tag) == expected, f"FreeCAD property {name} is outside the admitted box policy")


def empty(properties, name, kind, tag):
    row = child(properties[name], kind, tag)
    require(row["attributes"]["count"] == "0" and not row.get("children"),
            f"FreeCAD property {name} contains unsupported defined entries")


def identity(properties, name):
    row = child(properties[name], "Placement", "PropertyPlacement")["attributes"]
    translation = tuple(float(row[axis]) for axis in ("Px", "Py", "Pz"))
    quaternion = tuple(float(row[axis]) for axis in ("Q0", "Q1", "Q2", "Q3"))
    require(translation == (0, 0, 0) and quaternion[:3] == (0, 0, 0)
            and abs(quaternion[3]) == 1 and float(row["A"]) == 0.0,
            f"FreeCAD {name} requires explicit support placement")


def geo_properties(properties):
    for name in ("AttachmentOffset", "Placement"):
        identity(properties, name)
    default(properties, "BaseFeature", "Link", "Link", "")
    default(properties, "AttacherType", "String", "String", "Attacher::AttachEngine3D")
    default(properties, "MapMode", "Enumeration", "Integer", "0")
    default(properties, "MapReversed", "Bool", "Bool", "false")
    default(properties, "Refine", "Bool", "Bool", "false")
    default(properties, "Visibility", "Bool", "Bool", "true")
    default(properties, "Label2", "String", "String", "")
    empty(properties, "Support", "LinkSubList", "LinkSubList")
    empty(properties, "ExpressionEngine", "ExpressionEngine", "ExpressionEngine")
    require(float(value(properties, "MapPathParameter", "Float", "Float")) == 0,
            "FreeCAD attachment has an active path coordinate")


def box_dimensions(document, feature, properties):
    scalars = {}
    for item in document.parameters:
        key = item.attributes.get("freecad_path")
        require(isinstance(key, str) and key not in scalars and item.owner_id == feature.id and item.expression is None,
                "FreeCAD primitive contains a foreign, duplicate or expressed parameter")
        source_property = properties[key]
        require(item.attributes.get("freecad_property") == source_property
                and item.attributes.get("freecad_property_type") == source_property["attributes"]["type"],
                "FreeCAD neutral driver lost its actual source property")
        scalars[key] = item
    bound = tuple(scalars[key] for key in DIMENSIONS)
    measures = tuple(float(value(properties, key, "Length", "Float")) for key in DIMENSIONS)
    require(all(isfinite(size) and size > 0.0 and item.value.value == size and item.value.unit == "mm"
                and str(item.value.kind) == "length" and str(item.role) == "driving"
                for item, size in zip(bound, measures, strict=True)),
            "FreeCAD box does not carry three positive independent source dimensions")
    known_scalars = {"AttacherType", "Height", "Label", "Label2", "Length", "MapMode", "MapPathParameter",
                     "MapReversed", "Refine", "Visibility", "Width"}
    require(set(scalars) == known_scalars and {x.id for x in document.parameters} == set(feature.parameter_ids),
            "FreeCAD box contains a foreign driving property")
    return bound, measures


def box_semantics(document):
    AssertValid(document)
    require(document.source.format_id == "freecad.fcstd" and document.source.container_version == "1"
            and document.source.application_version.startswith("0.21") and document.source.attributes == {"freecad_schema_version": "4"}
            and str(document.units) == "mm", "expected the measured FreeCAD schema-four primitive source")
    require(set(document.metadata) == {"freecad"} and not (document.materials or document.sketches or document.selections
            or document.assembly or document.DrawingValue or document.meshes),
            "FreeCAD primitive includes another authored model domain")
    require(len(document.feature_timeline) == len(document.bodies) == len(document.configurations) == 1,
            "FreeCAD box translation requires one part body, one primitive and one active configuration")
    feature, body, config = document.feature_timeline[0], document.bodies[0], document.configurations[0]
    require(type(feature.definition) is NativeFeatureDefinition and feature.definition.type_id == "PartDesign::AdditiveBox"
            and str(feature.kind) == "primitive" and feature.sketch_id is None and not feature.suppressed,
            "FreeCAD feature is outside the origin-fixed AdditiveBox profile")
    require(body.final_feature_id == feature.id and body.material_id is None and config.active
            and config.parent_id is None and not (config.attributes or config.overrides or config.suppressed_feature_ids),
            "FreeCAD box lost actual body, material or configuration ownership")
    return feature, body, config


def check_body(body, part, properties):
    require(set(properties) == BODY_PROPERTIES, "FreeCAD Body property set differs")
    identity(properties, "Placement")
    default(properties, "BaseFeature", "Link", "Link", "")
    default(properties, "Label", "String", "String", body.name)
    default(properties, "Label2", "String", "String", "")
    default(properties, "Visibility", "Bool", "Bool", "true")
    empty(properties, "ExpressionEngine", "ExpressionEngine", "ExpressionEngine")
    default(properties, "Tip", "Link", "Link", part)
    default(properties, "Origin", "Link", "Link", "Origin")
    links = child(properties["Group"], "LinkList", "LinkList")
    require(links["attributes"]["count"] == "1" and len(links["children"]) == 1
            and links["children"][0]["tag"] == "Link" and links["children"][0]["attributes"]["value"] == part,
            "FreeCAD Body group owns another source feature")


def check_geometry(document, sizes):
    lx, ly, lz = sizes
    vertices = tuple(product((0.0, lx), (0.0, ly), (0.0, lz)))
    if document.brep is not None:
        shape = document.brep
        require(tuple(len(getattr(shape, name)) for name in ("vertices", "edges", "faces", "shells", "bodies"))
                == (8, 12, 6, 1, 1), "FreeCAD shape cache is inconsistent with an ordinary rectangular solid")
        points = tuple((v.point.x, v.point.y, v.point.z) for v in shape.vertices)
        require(all(sum(all(isclose(got, wanted, rel_tol=0, abs_tol=1e-10) for got, wanted in zip(point, corner, strict=True))
                        for point in points) == 1 for corner in vertices),
                "FreeCAD box cache is inconsistent with the independently computed origin and dimensions")
    return {"body_count": 1, "volume_m3": lx * ly * lz * 1e-9, "area_m2": 2 * (lx * ly + ly * lz + lz * lx) * 1e-6,
            "centre_m": [size / 2000 for size in sizes], "bounds_mm": [[0, 0, 0], list(sizes)],
            "source_cache_compared": document.brep is not None}


def source_text(document, body, feature, dimensions):
    original = document.metadata["freecad"]
    require(set(original) == {"document_properties", "entry_order", "file_version", "objects", "program_version", "schema_version"},
            "FreeCAD document carries a different source state inventory")
    require(original["program_version"] == document.source.application_version
            and original["file_version"] == document.source.container_version
            and original["schema_version"] == document.source.attributes["freecad_schema_version"],
            "FreeCAD document and source version owners disagree")
    records = original["document_properties"]["children"]
    properties = {row["attributes"]["name"]: row for row in records}
    require(len(properties) == len(records) and set(properties) == DOCUMENT_PROPERTIES,
            "FreeCAD source document contains an unqualified property set")
    for name in ("FileName", "Tip", "TransientDir"):
        require(properties[name]["tag"] == "_Property" and "children" not in properties[name],
                "FreeCAD transient document property has actual authored content")
    for name in ("Material", "Meta"):
        empty(properties, name, "Map", "Map")
    require(value(properties, "ShowHidden", "Bool", "Bool") == "false", "FreeCAD hidden-object policy is active")
    names = ("Comment", "Company", "CreatedBy", "CreationDate", "Id", "Label", "LastModifiedBy", "LastModifiedDate",
             "License", "LicenseURL", "TipName")
    raw = {name: value(properties, name, "String", "String") for name in names}
    require(raw["Label"] and not raw["TipName"], "FreeCAD source has no label or has an unsupported document tip")
    uid = value(properties, "Uid", "UUID", "Uuid")
    require(str(UUID(uid)) == uid, "FreeCAD source identity is outside the measured UUID form")
    creation = datetime.fromisoformat(raw["CreationDate"])
    modified = datetime.fromisoformat(raw["LastModifiedDate"])
    require(creation.tzinfo is not None and modified.tzinfo is not None,
            "FreeCAD authored dates must be explicit")
    summary = {label: raw[key] for key, label in (("Label", "title"), ("Comment", "comments"), ("CreatedBy", "author")) if raw[key]}
    extra = {"FreeCAD " + name: raw[name] for name in ("Company", "CreationDate", "Id", "LastModifiedBy", "LastModifiedDate",
                                                       "License", "LicenseURL") if raw[name]}
    extra.update({"FreeCAD Uid": uid, "FreeCAD Body Label": body.name, "FreeCAD Feature Id": feature.id,
                  "FreeCAD Source Version": document.source.application_version,
                  "FreeCAD Source Schema": original["schema_version"], "FreeCAD Show Hidden": "false"})
    extra.update({"FreeCAD " + name + " Parameter": item.id for name, item in zip(DIMENSIONS, dimensions, strict=True)})
    return raw["Label"], PartTextInput(summary, extra, {}), int(creation.timestamp())


def lower_box(document, name, feature, body, config, parameters, sizes):
    draft = MakeCornerDoc(name, *sizes)
    source_sketch, source_feature = draft.sketches[0], draft.feature_timeline[0]
    sketch_name = feature.name + " Profile"
    sketch_id = feature.id + ":profile"
    source_param_ids = {role: owner.id for role, owner in zip(("parameter/width", "parameter/height", "parameter/depth"), parameters, strict=True)}
    plane = next(plane for plane in document.support_planes if plane.name == "XY-plane")
    support = replace(draft.support_planes[0], id=plane.id)
    relations = tuple(replace(item, parameter_id=source_param_ids[item.parameter_id]) if item.parameter_id else item
                      for item in source_sketch.constraints)
    sketch = replace(source_sketch, id=sketch_id, name=sketch_name, support_plane_id=support.id,
                     constraints=relations, parameter_ids=tuple(source_param_ids[key] for key in source_sketch.parameter_ids))
    native_parameters = tuple(replace(item, id=source_param_ids[item.id], owner_id=sketch.id if item.owner_id == source_sketch.id else feature.id)
                              for item in draft.parameters)
    operation = replace(source_feature, id=feature.id, name=feature.name, sketch_id=sketch.id,
                        parameter_ids=(source_param_ids["parameter/depth"],))
    solid = replace(draft.bodies[0], id=body.id, name=operation.name, final_feature_id=operation.id)
    lowered = replace(draft, source=document.source, configurations=(config,), support_planes=(support,),
                      sketches=(sketch,), feature_timeline=(operation,), parameters=native_parameters, bodies=(solid,))
    bindings = {parameters[0].id: "D1@" + sketch.name, parameters[1].id: "D2@" + sketch.name,
                parameters[2].id: "D1@" + operation.name}
    AssertValid(lowered)
    return lowered, bindings


def project(document):
    feature, body, config = box_semantics(document)
    data = feature.definition.object_data
    part = data["name"]
    properties = data["properties"]
    require(set(properties) == FEATURE_PROPERTIES and data["type_id"] == "PartDesign::AdditiveBox" and not data["touched"],
            "FreeCAD primitive property layout differs from the documented profile")
    require(data["extensions"] == [{"attributes": {"name": "AttachExtension", "type": "Part::AttachExtension"}, "tag": "Extension"}]
            and data["dependencies"] == [body.attributes["freecad"]["name"]],
            "FreeCAD primitive uses another attachment engine or owner")
    require({plane.name for plane in document.support_planes} == set(AXIS_ROLES)
            and len(document.support_planes) == 3,
            "FreeCAD primitive does not carry the actual three origin datums")
    for plane in document.support_planes:
        frame = plane.transform
        actual = tuple((item.x, item.y, item.z) for item in (frame.x_axis, frame.y_axis, frame.z_axis))
        require(frame.origin.x == frame.origin.y == frame.origin.z == 0 and actual == PLANE_FRAMES[plane.name]
                and plane.support_selection_id is None and plane.offset_parameter_id is None,
                "FreeCAD datum is no longer an ordinary origin plane")
    objects = document.metadata["freecad"]["objects"]
    expected = {body.attributes["freecad"]["name"]: "PartDesign::Body", part: "PartDesign::AdditiveBox", "Origin": "App::Origin",
                **{axis + "_Axis": "App::Line" for axis in ("X", "Y", "Z")},
                **{plane + "_Plane": "App::Plane" for plane in ("XY", "XZ", "YZ")}}
    require({row["name"]: row["type_id"] for row in objects} == expected and len(objects) == len(expected),
            "FreeCAD source includes another modeled object")
    default(properties, "Label", "String", "String", feature.name)
    geo_properties(properties)
    check_body(body, part, body.attributes["freecad"]["properties"])
    owners, sizes = box_dimensions(document, feature, properties)
    geometry = check_geometry(document, sizes)
    name, text, creation = source_text(document, body, feature, owners)
    lowered, bindings = lower_box(document, name, feature, body, config, owners, sizes)
    return BoxProjection(lowered, text, sizes, creation, bindings, body.name, feature.name, geometry)
