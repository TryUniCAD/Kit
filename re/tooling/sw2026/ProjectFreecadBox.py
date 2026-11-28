from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from itertools import product
from math import isclose, isfinite, pi, sqrt
from uuid import UUID

from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.PartTextInput import PartTextInput
from convert.adapters.solidworks.Archive.Construction.Units.UnitInput import UnitInput
from convert.adapters.solidworks.Core.Preparation.FreecadBox.LowerBoxModel import LowerBoxModel
import FreecadBoxRelease as release_fields
from FreecadBoxRelease import child, require, value
from interchange import CadDocument, NativeFeatureDefinition
from interchange.document.Validation.DocumentValidate import AssertValid


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
    unit_recipe: UnitInput | None
    attached_top: bool


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


def geo_properties(properties, version, attached_top):
    identity(properties, "AttachmentOffset")
    support = "Support" if version == "0.21" else "AttachmentSupport"
    if attached_top:
        placement = child(properties["Placement"], "Placement", "PropertyPlacement")["attributes"]
        half_angle = sqrt(0.5)
        require(
            tuple(float(placement[key]) for key in ("Px", "Py", "Pz", "Ox", "Oy", "Oz"))
            == (0.0, 0.0, 0.0, 1.0, 0.0, 0.0)
            and all(isclose(float(placement[key]), target, abs_tol=1e-14, rel_tol=0.0)
                    for key, target in zip(("Q0", "Q1", "Q2", "Q3", "A"),
                                           (half_angle, 0.0, 0.0, half_angle, pi / 2), strict=True)),
            "FreeCAD attached box does not resolve to a positive quarter-turn about model X",
        )
        link = child(properties[support], "LinkSubList", "LinkSubList")
        require(
            link["attributes"] == {"count": "1"}
            and link["children"] == [{"tag": "Link", "attributes": {"obj": "XZ_Plane", "sub": ""}}],
            "FreeCAD attached box must select exactly its actual whole XZ plane",
        )
    else:
        identity(properties, "Placement")
        empty(properties, support, "LinkSubList", "LinkSubList")
    default(properties, "BaseFeature", "Link", "Link", "")
    default(properties, "AttacherType", "String", "String", "Attacher::AttachEngine3D")
    default(properties, "MapMode", "Enumeration", "Integer", "5" if attached_top else "0")
    default(properties, "MapReversed", "Bool", "Bool", "false")
    refine = value(properties, "Refine", "Bool", "Bool")
    require(refine in (("false",) if version == "0.21" else ("false", "true")),
            "FreeCAD box has an unqualified refinement state")
    default(properties, "Visibility", "Bool", "Bool", "true")
    default(properties, "Label2", "String", "String", "")
    empty(properties, "ExpressionEngine", "ExpressionEngine", "ExpressionEngine")
    require(float(value(properties, "MapPathParameter", "Float", "Float")) == 0,
            "FreeCAD attachment has an active path coordinate")
    if version != "0.21":
        require(release_fields.caption(properties, "AttacherEngine") == "Engine 3D",
                "FreeCAD box has an unqualified named attachment engine")
        default(properties, "Suppressed", "Bool", "Bool", "false")
        suppressed_shape = properties["SuppressedShape"]
        require(suppressed_shape["tag"] == "Property"
                and suppressed_shape["attributes"]["type"] == "Part::PropertyPartShape",
                "FreeCAD suppression cache has an unqualified property type")
    if version == "1.1":
        require(float(value(properties, "FuzzyTolerance", "FloatConstraint", "Float")) == -1.0,
                "FreeCAD box has an active fuzzy tolerance")


def box_dimensions(document, feature, properties, version):
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
    if version != "0.21":
        known_scalars |= release_fields.FEATURE_SCALARS
    if version == "1.1":
        known_scalars.add("FuzzyTolerance")
    require(set(scalars) == known_scalars and {x.id for x in document.parameters} == set(feature.parameter_ids),
            "FreeCAD box contains a foreign driving property")
    if version != "0.21":
        require(scalars["AttacherEngine"].value.value == "Engine 3D" and scalars["Suppressed"].value.value is False
                and scalars["Refine"].value.value == (value(properties, "Refine", "Bool", "Bool") == "true"),
                "FreeCAD box carries an inconsistent attachment, refinement or suppression owner")
    if version == "1.1":
        require(scalars["FuzzyTolerance"].value.value == -1.0,
                "FreeCAD box carries an inconsistent neutral tolerance owner")
    return bound, measures


def box_semantics(document, version):
    AssertValid(document)
    require(document.source.format_id == "freecad.fcstd" and document.source.container_version == "1"
            and version is not None and document.source.attributes == {"freecad_schema_version": "4"}
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


def check_body(body, part, properties, version):
    expected = BODY_PROPERTIES if version == "0.21" else BODY_PROPERTIES | release_fields.BODY_PROPERTIES
    require(set(properties) == expected, "FreeCAD Body property set differs")
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
    if version != "0.21":
        compound = value(properties, "AllowCompound", "Bool", "Bool")
        require(compound in ("false", "true"), "FreeCAD Body has a malformed compound setting")
        return {"FreeCAD Body Allows Compound": compound, "FreeCAD Body Material UUID": release_fields.material_id(properties)}
    return {}


def check_geometry(document, sizes, attached_top):
    lx, ly, lz = sizes
    minimum = (0.0, -lz, 0.0) if attached_top else (0.0, 0.0, 0.0)
    maximum = (lx, 0.0, ly) if attached_top else sizes
    vertices = tuple(product(*zip(minimum, maximum, strict=True)))
    if document.brep is not None:
        shape = document.brep
        require(tuple(len(getattr(shape, name)) for name in ("vertices", "edges", "faces", "shells", "bodies"))
                == (8, 12, 6, 1, 1), "FreeCAD shape cache is inconsistent with an ordinary rectangular solid")
        points = tuple((v.point.x, v.point.y, v.point.z) for v in shape.vertices)
        require(all(sum(all(isclose(got, wanted, rel_tol=0, abs_tol=1e-10) for got, wanted in zip(point, corner, strict=True))
                        for point in points) == 1 for corner in vertices),
                "FreeCAD box cache is inconsistent with the independently computed origin and dimensions")
    return {"body_count": 1, "volume_m3": lx * ly * lz * 1e-9, "area_m2": 2 * (lx * ly + ly * lz + lz * lx) * 1e-6,
            "centre_m": [(low + high) / 2000 for low, high in zip(minimum, maximum, strict=True)],
            "bounds_mm": [list(minimum), list(maximum)],
            "source_cache_compared": document.brep is not None}


def source_text(document, body, feature, dimensions, version, flags):
    original = document.metadata["freecad"]
    schema = {"document_properties", "entry_order", "file_version", "objects", "program_version", "schema_version"}
    if version != "0.21":
        schema.add("string_hasher")
    require(set(original) == schema,
            "FreeCAD document carries a different source state inventory")
    require(original["program_version"] == document.source.application_version
            and original["file_version"] == document.source.container_version
            and original["schema_version"] == document.source.attributes["freecad_schema_version"],
            "FreeCAD document and source version owners disagree")
    records = original["document_properties"]["children"]
    properties = {row["attributes"]["name"]: row for row in records}
    expected = DOCUMENT_PROPERTIES if version == "0.21" else DOCUMENT_PROPERTIES | release_fields.DOCUMENT_PROPERTIES
    require(len(properties) == len(records) and set(properties) == expected,
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
    units = None
    if version != "0.21":
        release_fields.cache_document(original)
        units, preferences = release_fields.document_units(properties)
        extra.update(preferences)
    extra.update(flags)
    return raw["Label"], PartTextInput(summary, extra, {}), int(creation.timestamp()), units


def source_origin(objects, expected, version):
    known = {row["name"]: row for row in objects}
    if version == "1.1":
        expected = expected | {"Origin001": "App::Point"}
    require({name: row["type_id"] for name, row in known.items()} == expected and len(objects) == len(expected),
            "FreeCAD source includes another modeled object")
    if version != "1.1":
        return {}
    origin = known["Origin"]
    owned = tuple(name for name, kind in expected.items() if kind in ("App::Line", "App::Plane", "App::Point"))
    children = child(origin["properties"]["OriginFeatures"], "LinkList", "LinkList")
    require(children["attributes"]["count"] == str(len(owned))
            and tuple(row["attributes"]["value"] for row in children["children"] if row["tag"] == "Link") == owned
            and origin["dependencies"] == list(owned) and not origin["touched"],
            "FreeCAD origin has another owned source datum")
    identity(origin["properties"], "Placement")
    row = known["Origin001"]
    point = row["properties"]
    require(set(point) == {"ExpressionEngine", "Label", "Label2", "Placement", "Role", "Visibility"}
            and not (row["touched"] or row["dependencies"] or row["extensions"]),
            "FreeCAD origin point has an unqualified property or owner")
    identity(point, "Placement")
    empty(point, "ExpressionEngine", "ExpressionEngine", "ExpressionEngine")
    default(point, "Role", "String", "String", "Origin")
    default(point, "Label2", "String", "String", "")
    default(point, "Visibility", "Bool", "Bool", "true")
    return {"FreeCAD Origin Point Id": row["name"], "FreeCAD Origin Point Label": value(point, "Label", "String", "String")}


def project(document, *, source_labels=False, attached_top=False):
    version = release_fields.release(document.source.application_version)
    feature, body, _ = box_semantics(document, version)
    data = feature.definition.object_data
    part = data["name"]
    properties = data["properties"]
    expected_properties = FEATURE_PROPERTIES
    if version != "0.21":
        expected_properties = (FEATURE_PROPERTIES - {"Support"}) | release_fields.FEATURE_PROPERTIES
    if version == "1.1":
        expected_properties |= {"FuzzyTolerance"}
    require(set(properties) == expected_properties and data["type_id"] == "PartDesign::AdditiveBox" and not data["touched"],
            "FreeCAD primitive property layout differs from the documented profile")
    dependencies = [body.attributes["freecad"]["name"]]
    if attached_top:
        dependencies.append("XZ_Plane")
    require(data["extensions"] == release_fields.extensions(version)
            and data["dependencies"] == dependencies,
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
    origin_properties = source_origin(objects, expected, version)
    default(properties, "Label", "String", "String", feature.name)
    geo_properties(properties, version, attached_top)
    body_properties = check_body(body, part, body.attributes["freecad"]["properties"], version)
    flags = body_properties | origin_properties
    if attached_top:
        support = next(plane for plane in document.support_planes if plane.name == "XZ-plane")
        flags.update({"FreeCAD Attachment Support Id": support.id, "FreeCAD Attachment Map Mode": "5"})
    if version != "0.21":
        flags.update({"FreeCAD Feature Material UUID": release_fields.material_id(properties),
                      "FreeCAD Feature Refine": value(properties, "Refine", "Bool", "Bool")})
    if version == "1.1":
        flags["FreeCAD Feature Fuzzy Tolerance"] = value(properties, "FuzzyTolerance", "FloatConstraint", "Float")
    owners, sizes = box_dimensions(document, feature, properties, version)
    geometry = check_geometry(document, sizes, attached_top)
    name, text, creation, units = source_text(document, body, feature, owners, version, flags)
    lowered = LowerBoxModel(
        document, name, tuple(item.id for item in owners), sizes,
        DIMENSIONS if source_labels else ("D1", "D2", "D1"),
        body.name if source_labels else feature.name,
        TopAttached=attached_top,
    )
    owner_names = {item.id: item.name for item in (*lowered.sketches, *lowered.feature_timeline)}
    bindings = {item.id: item.name + "@" + owner_names[item.owner_id] for item in lowered.parameters}
    return BoxProjection(lowered, text, sizes, creation, bindings, body.name, feature.name, geometry, units, attached_top)
