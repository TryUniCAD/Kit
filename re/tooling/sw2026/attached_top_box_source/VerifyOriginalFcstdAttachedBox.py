from argparse import ArgumentParser
from base64 import b64decode, b64encode
from codecs import lookup
from contextlib import contextmanager
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from io import BytesIO
from itertools import product
import json
from math import isclose, isfinite
from pathlib import Path, PureWindowsPath
import subprocess
import sys
from tempfile import TemporaryDirectory
from xml.etree.ElementTree import fromstring
from zipfile import ZipFile


HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(ROOT / "src"), str(ROOT), str(HERE.parent)]

from BoxIncidence import box_incidence, cross, require, xyz
from convert import open_document, write_document
from convert.adapters.base.WritePolicy import GetDocumentCaps
from convert.adapters.registry.RegistryErrors import NotFoundError
from convert.adapters.solidworks.Archive.Construction.PlanarMates.ReadDatumFrame import ReadDatumFrame
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Preparation.FreecadBox.MakeOriginBoxPart import MakeOriginBox
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.ReadBoxGeometry import CheckBoxCache
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.ReadBoxSource import ReadBoxSource
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ColdOutput.ReadColdOutput import ReadColdOutput
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismFrame import ReadPrismFrame
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.CheckDimGraph import CheckDimGraph
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadLineDims import ReadLineDims
from convert.adapters.solidworks.Core.TypedResolved.Lines.ReadLineLoop import ReadLineLoop
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
from convert.Geometry.Opencascade import decode_ascii_brep
from interchange.document.Models.DocumentProvenance import IterProvenance
from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit


SOURCE_SHA = "25c836424406343439bd3fa9acd82f8e6dbabdae689fe2a799099bf73805aafb"
NATIVE_SHA = "3b16c1abb7dd6240c4adb46e340f7b1167531a750553420bfc03b9f7139d2a89"
SHARED_SHA = "46bc4ae57efcd132d99b880b0e95c6ba70bf2a468c450f6a6dddc0435b2a9bfc"
CASE = "recipe-0.21.2-F14c"
LOCATOR = r"C:\KitAttachedTopBoxGenerated01\recipe-0.21.2-F14c\F14c.SLDPRT"
FORMAT = "solidworks.sldprt"
DRIVERS = ("Length", "Width", "Height")
DATUMS = {"XY_Plane": "Front Plane", "XZ_Plane": "Top Plane", "YZ_Plane": "Right Plane"}
CAPS = {"body_structure", "brep", "configurations", "native_payloads", "parameters",
        "parametric_history", "provenance", "roundtrip_metadata", "support_planes"}
NO_TRANSFER = ["native_payloads", "provenance", "roundtrip_metadata"]


def digest(data):
    return sha256(data).hexdigest()


def locked(path, expected):
    data = path.read_bytes()
    require(digest(data) == expected, "immutable source or receipt identity differs")
    return data


def select(root, path):
    child, = root.findall(path)
    return child


def prop(node, name, tag):
    return select(node, f"./Properties/Property[@name='{name}']/{tag}")


def source_owners(root, document):
    require(root.attrib == {"FileVersion": document.source.container_version,
                           "SchemaVersion": "4", "ProgramVersion": document.source.application_version},
            "release or schema identity differs from the strict source")
    owners = {row["name"]: row for row in document.metadata["freecad"]["objects"]}
    xml_owners = root.findall("./Objects/Object")
    require(len(xml_owners) == len(owners) == 9
            and [(x.attrib["name"], x.attrib["type"], x.attrib["id"]) for x in xml_owners]
            == [(x["name"], x["type_id"], x["object_id"]) for x in owners.values()],
            "typed owner inventory differs from its original XML declarations")
    for name, owner in owners.items():
        dependency, = root.findall(f"./Objects/ObjectDeps[@Name='{name}']")
        require(int(dependency.attrib["Count"]) == len(dependency)
                and all(row.tag == "Dep" for row in dependency)
                and [row.attrib["Name"] for row in dependency] == owner["dependencies"],
                "typed dependency order differs from its source declaration")
    return {name: {"object_id": row["object_id"], "type_id": row["type_id"],
                   "dependencies": row["dependencies"]} for name, row in owners.items()}


def rotation_frame(properties):
    position = tuple(float(properties[key]) for key in ("Px", "Py", "Pz"))
    axes = tuple(float(properties[key]) for key in ("Ox", "Oy", "Oz"))
    qx, qy, qz, scalar = (float(properties[key]) for key in ("Q0", "Q1", "Q2", "Q3"))
    require(position == (0.0, 0.0, 0.0) and axes == (1.0, 0.0, 0.0)
            and isclose(qx*qx+qy*qy+qz*qz+scalar*scalar, 1.0, rel_tol=0.0, abs_tol=1e-14),
            "source attachment is not the ordinary origin rotation")
    imaginary = (qx, qy, qz)
    def rotate(point):
        first = cross(imaginary, point)
        second = cross(imaginary, first)
        return tuple(x + 2.0 * (scalar*u + v) for x, u, v in zip(point, first, second, strict=True))
    return rotate


def source_intent(root, document):
    body, = document.bodies
    feature, = document.feature_timeline
    body_name = body.attributes["freecad"]["name"]
    feature_name = feature.definition.object_data["name"]
    body_xml = select(root, f"./ObjectData/Object[@name='{body_name}']")
    feature_xml = select(root, f"./ObjectData/Object[@name='{feature_name}']")
    require(prop(body_xml, "Tip", "Link").get("value") == feature_name
            and [row.get("value") for row in prop(body_xml, "Group", "LinkList")] == [feature_name]
            and prop(body_xml, "Origin", "Link").get("value") == "Origin"
            and body.final_feature_id == feature.id
            and [row.attrib for row in prop(feature_xml, "Support", "LinkSubList")]
            == [{"obj": "XZ_Plane", "sub": ""}], "source is missing its live body, datum or origin")
    dimensions = tuple(float(prop(feature_xml, name, "Float").get("value")) for name in DRIVERS)
    require(all(isfinite(value) and value > 0 for value in dimensions), "source lacks three positive dimensions")
    driver_rows = {}
    for name, value in zip(DRIVERS, dimensions, strict=True):
        parameter, = (row for row in document.parameters if row.attributes["freecad_path"] == name)
        require(parameter.owner_id == feature.id and parameter.id in feature.parameter_ids
                and parameter.role == "driving" and parameter.expression is None
                and parameter.value.value == value and parameter.value.unit == "mm",
                "source dimension is not a real driving parameter of the attached feature")
        driver_rows[name] = {"source_id": parameter.id, "value_mm": value}
    ordered_corners = tuple(product(*((0.0, value) for value in dimensions)))
    placement = prop(feature_xml, "Placement", "PropertyPlacement").attrib
    rotate = rotation_frame(placement)
    config, = document.configurations
    datums = {}
    for datum in document.support_planes:
        native_name = datum.attributes["principal_role"]
        frame = datum.transform
        datums[native_name] = {"source_id": datum.id, "target_name": DATUMS[native_name], "origin": xyz(frame.origin),
                               "basis": tuple(map(xyz, (frame.x_axis, frame.y_axis, frame.z_axis)))}
    require(len(document.support_planes) == len(datums) == len(DATUMS),
            "source principal datum inventory differs")
    return {
        "body_id": body.id, "body_name": body.name, "feature_id": feature.id, "feature_name": feature.name,
        "support_plane_id": "freecad:plane:XZ_Plane", "configuration": config.name, "drivers": driver_rows,
        "datums": datums,
        "placement_quaternion": [float(placement["Q" + str(i)]) for i in range(4)],
        "local_corners": ordered_corners, "world_corners": tuple(map(rotate, ordered_corners)),
    }, ((body_name, "Shape", body_xml), (feature_name, "AddSubShape", feature_xml),
        (feature_name, "Shape", feature_xml))


def read_payloads(document, raw, archive, xml, shape_roles, intent):
    rows = {row.id: row for row in document.brep_payloads}
    shape_ids = [f"freecad:brep:{name}:{field}" for name, field, _ in shape_roles]
    doc_id, binding_id = ("freecad:native-document", "freecad:native-document-binding")
    require(len(rows) == len(document.brep_payloads) == 5 and set(rows) == {*shape_ids, doc_id, binding_id},
            "source includes a missing or additional payload owner")
    full, binding = rows[doc_id], rows[binding_id]
    span, = full.provenance.spans
    require(full.role == "document" and full.data == raw and full.sha256 == document.source.sha256
            and (span.stream, span.offset, span.length, span.record_kind) == ("Document.xml", 0, len(xml), "xml")
            and binding.role == "verification" and binding.data == bytes.fromhex(full.sha256)
            and binding.sha256 == digest(binding.data),
            "source document and native SHA binding are not the actual input")
    source_body, = document.bodies
    source_feature, = document.feature_timeline
    require(source_body.attributes["brep_payload_ids"] == shape_ids[:1]
            and source_feature.attributes["brep_payload_ids"] == shape_ids[1:],
            "source B-rep references differ from their typed body and feature owners")
    proof = {}
    signatures = []
    streams = ["Document.xml"]
    for (name, field, node), shape_id in zip(shape_roles, shape_ids, strict=True):
        payload = rows[shape_id]
        part = prop(node, field, "Part")
        stream = part.attrib["file"]
        data = archive.read(stream)
        require(payload.role == "brep" and payload.format_id == "opencascade"
                and payload.source_stream == stream and payload.data == data and digest(data) == payload.sha256
                and payload.provenance.native_id == name + "." + field
                and payload.attributes["freecad_object"] == name and payload.attributes["freecad_property"] == field
                and payload.attributes["freecad_part_attributes"] == part.attrib == {"file": stream}
                and "freecad_sidecars" not in payload.attributes,
                "source shape bytes or cache owner differ from their XML member")
        require(payload.attributes.get("body_id") == (source_body.id if shape_id == shape_ids[0] else None)
                and payload.attributes.get("feature_id") == (source_feature.id if shape_id == shape_ids[2] else None),
                "source shape carries the wrong active body or result feature identity")
        local = field == "AddSubShape"
        decoded = decode_ascii_brep(data, id_prefix=shape_id)
        require(decoded is not None, "the actual source owner has no independently readable B-rep")
        solid, signature = box_incidence(decoded, intent["local_corners" if local else "world_corners"])
        proof[shape_id] = {"stream": stream, "sha256": payload.sha256, "bytes": len(data),
                           "coordinates": "feature-local" if local else "model", "decoded_solid_id": solid}
        signatures.append(signature)
        streams.append(stream)
    body_solid, signature = box_incidence(document.brep, intent["world_corners"], source_body.id)
    require(all(value == signature for value in signatures)
            and document.brep.bodies[0].attributes["brep_payload_id"] == shape_ids[0]
            and document.brep.bodies[0].attributes["feature_id"] == source_feature.id
            and archive.namelist() == streams and document.metadata["freecad"]["entry_order"] == streams[1:],
            "source shape incidence, selected body or archive payload inventory differs")
    return {"shape_owners": proof, "incidence": signature, "parsed_body_id": body_solid,
            "document_xml_sha256": digest(xml), "native_binding_sha256": binding.sha256}


def source_proof(document, raw):
    require(document.source.sha256 == digest(raw) and {cap.value for cap in GetDocumentCaps(document)} == CAPS,
            "source identity or full capability inventory differs")
    with ZipFile(BytesIO(raw)) as archive:
        xml = archive.read("Document.xml")
        root = fromstring(xml)
        owners = source_owners(root, document)
        intent, shape_roles = source_intent(root, document)
        payloads = read_payloads(document, raw, archive, xml, shape_roles, intent)
    return {**intent, **payloads, "object_owners": owners,
            "source_provenance_owners": sorted(row.native_id for row in IterProvenance(document))}


def refusal(check, message):
    try:
        check()
    except ValueError as error:
        require(str(error) == message, "wrong scoped refusal: " + str(error))
        return str(error)
    raise ValueError("a changed source passed its guard")


def negatives(document, raw, source):
    body_cache, _, result_cache, *_ = document.brep_payloads
    payloads = (replace(body_cache, data=result_cache.data, sha256=result_cache.sha256), *document.brep_payloads[1:])
    changed = replace(document, brep_payloads=payloads)
    omitted = replace(document, brep_payloads=document.brep_payloads[1:])
    edge = document.brep.edges[0]
    bad_body = replace(document.brep, edges=(replace(edge, start_vertex_id=edge.end_vertex_id), *document.brep.edges[1:]))
    corners = source["world_corners"]
    bounds = tuple(tuple(combine(point[i] for point in corners) for i in range(3)) for combine in (min, max))
    CheckBoxCache(bad_body, *bounds)
    extra_domain = replace(document, metadata={**document.metadata, "extra_owner": True})
    return {
        "equal_shape_bytes_crossed_between_owners": refusal(lambda: source_proof(changed, raw),
            "source shape bytes or cache owner differ from their XML member"),
        "missing_shape_owner": refusal(lambda: source_proof(omitted, raw),
            "source includes a missing or additional payload owner"),
        "invalid_incidence_with_same_corner_counts": refusal(lambda: box_incidence(
            bad_body, corners, source["body_id"]), "decoded boundary is invalid"),
        "additional_source_scope": refusal(lambda: ReadBoxSource(extra_domain),
            "FreeCAD primitive includes another authored model domain"),
    }


def public_refusals(document, target, locator):
    missing = sorted(cap.value for cap in GetDocumentCaps(document) - SldprtWriter().info.Capabilities)
    require(missing == NO_TRANSFER, "public capability contract has changed")
    stream = BytesIO()
    options = {"require_native_transfers": True}
    calls = (
        ("inferred_path", target, None, options),
        ("explicit_path", target, FORMAT, options),
        ("explicit_stream", stream, FORMAT, {**options, "final_destination": locator}),
    )
    result = {}
    for name, sink, fmt, values in calls:
        try:
            write_document(document, sink, destination_format=fmt, values=values, allow_carrier=False)
        except NotFoundError as error:
            result[name] = str(error)
        else:
            raise ValueError("the intact original unexpectedly reached public writing")
    require(not stream.getvalue(), "rejected public writer mutated caller stream bytes")
    return {"refusals": result, "unrepresented_capabilities": missing, "published_bytes": 0}


@contextmanager
def guarded(scratch=None):
    audit = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
    audit.BeginBuild()
    active = True
    denied = []
    def inspect(event, args):
        if not active:
            return
        if event in {"tempfile.mkdtemp", "os.mkdir", "os.remove", "os.rename", "ctypes.dlopen"} or event.startswith("socket."):
            denied.append(event)
            raise PermissionError("runtime write, staging or external access")
        audit.InspectEvent(event, args)
    sys.addaudithook(inspect)
    try:
        yield
    finally:
        active = False
    require(not denied and not audit.DeniedReads, "runtime guard was reached")
    if scratch is not None:
        require(not any(scratch.iterdir()), "public refusal created a staging or destination entry")


def prewarm():
    for name in ("utf-16", "utf-16-le", "utf-8", "latin-1"):
        lookup(name)
    for name in ("DocumentAssemblyValidate", "DocumentFeatureValidate", "DocumentReferenceValidate"):
        import_module("interchange.document.Validation." + name)
    for name in ("DocumentProvenance", "DocumentWalk"):
        import_module("interchange.document.Models." + name)
    import_module("interchange.document.Behavior.DocumentIo")


def generate(data):
    path = Path(data["source"])
    raw = locked(path, data["source_sha256"])
    document = open_document(path)
    prewarm()
    with TemporaryDirectory(prefix="KitF14cOwnerGuard.") as folder:
        root = Path(folder)
        with guarded(root):
            source = source_proof(document, raw)
            faults = negatives(document, raw, source)
            plan = ReadBoxSource(document)
            require(plan.ModelValue.source == document.source and plan.ModelValue.brep is None
                    and not plan.ModelValue.brep_payloads and plan.PropertiesValue.ConfigurationFields == {},
                    "construction did not receive the projected semantic model and source identity only")
            candidate = MakeOriginBox(plan.ModelValue, data["locator"], plan.CreationEpoch, plan.PropertiesValue,
                                      UnitsValue=plan.UnitsValue, TopAttached=True)
            final_target = root / "uncreated" / PureWindowsPath(data["locator"]).name
            denied = public_refusals(document, final_target, data["locator"])
    locked(path, data["source_sha256"])
    properties = {"summary": dict(plan.PropertiesValue.SummaryFields), "document": dict(plan.PropertiesValue.DocumentFields)}
    return {"source": source, "refusals": faults, "public_write": denied, "projected_properties": properties,
            "creation_epoch": plan.CreationEpoch, "source_sha256": digest(raw),
            "artifact": {"bytes": len(candidate.BytesValue), "sha256": digest(candidate.BytesValue),
                         "streams": {key: {"bytes": len(value), "sha256": digest(value)}
                                     for key, value in candidate.StreamsValue.items()}},
            "candidate_b64": b64encode(candidate.BytesValue).decode(), "runtime_data_file_reads": 0}


def target_drivers(document, link, owner, source, sketch):
    dims = ReadLineDims(sketch, link)
    loop = ReadLineLoop(sketch, link, dims)
    CheckDimGraph(loop, dims)
    anchor = dims.OriginValue
    require(anchor is not None and anchor.PositionValue == (0.0, 0.0)
            and anchor.LocalIndex != anchor.ExternalIndex
            and loop.PointsValue[anchor.LocalIndex].PositionValue == (0.0, 0.0)
            and ReadNativeName(anchor.FeatureValue) == "Origin",
            "target rectangle has no actual corner relation to the model origin")
    depth = owner.RequireDepth().DepthValue
    require(len(dims.DriverValues) == 2 and depth.name == "Height", "target has a different finite driver set")
    inputs = source["drivers"]
    planar = {}
    for dimension in dims.DriverValues:
        name = dimension.NameValue
        index = 0 if name == "Length" else 1
        actual_points = [loop.PointsValue[point].PositionValue for point in dimension.PointValues]
        expected_other = (inputs["Length"]["value_mm"], 0.0) if index == 0 else (0.0, -inputs["Width"]["value_mm"])
        require(name in DRIVERS[:2] and anchor.LocalIndex in dimension.PointValues
                and set(actual_points) == {(0.0, 0.0), expected_other},
                "target active sketch driver has the wrong signed endpoint owners")
        planar[name] = (dimension.ParamOwner, dimension.NodeValue.FieldsValue["f50"],
                        NativeNodeId(owner.ProfileValue), dimension.MetresValue * 1000.0, dimension.PointValues)
    measurements = {**planar, "Height": (depth.TypedOwner, depth.TypedOwner["dimension_id"],
                                        NativeNodeId(owner.NodeValue), depth.value_mm, None)}
    drivers = {row.name: row for row in document.parameters}
    require(len(document.parameters) == 3 and set(drivers) == set(measurements) == set(DRIVERS),
            "public target parameter inventory differs")
    features = {row.id: row for row in document.feature_timeline}
    for name, (span, identity, feature_id, value, points) in measurements.items():
        parameter = drivers[name]
        public_span, = parameter.provenance.spans
        require(parameter.owner_id == f"sldprt:feature:{feature_id}"
                and parameter.id in features[parameter.owner_id].parameter_ids and parameter.role == "driving"
                and parameter.value.unit == "mm" and parameter.expression is None
                and parameter.value.value == value == inputs[name]["value_mm"]
                and (public_span.stream, public_span.offset, public_span.offset + public_span.length)
                == (span["stream"], span["offset"], span["end"]),
                "public target driver differs from its exact live parameter owner")
        inputs[name].update(target_id=parameter.id, target_parameter_index=span["object_index"],
                            target_dimension_id=identity, sketch_point_indices=points)
    return NativeNodeId(anchor.FeatureValue)


def target_datums(document, roots, profile, source, plane_id):
    planes = {ReadNativeName(row): row for row in roots.values() if row.ClassValue.NameValue == "moRefPlane_c"}
    public = {row.name: row for row in document.support_planes}
    require(len(public) == len(planes) == len(source["datums"]), "target datum inventory differs")
    sketch, = document.sketches
    result = {}
    for expectation in source["datums"].values():
        name = expectation["target_name"]
        native = planes[name]
        public_plane = public[name]
        frame, _ = ReadDatumFrame(native)
        identity = NativeNodeId(native)
        actual = public_plane.transform
        basis = (frame.AxisU, frame.AxisV, frame.NormalValue)
        require(list(frame.OriginValue) == expectation["origin"] and xyz(actual.origin) == frame.OriginValue
                and [list(value) for value in basis] == expectation["basis"]
                and tuple(map(xyz, (actual.x_axis, actual.y_axis, actual.z_axis))) == basis
                and public_plane.id == f"sldprt:plane:{identity}",
                "target datum lost its authenticated input frame")
        if expectation["source_id"] == source["support_plane_id"]:
            require(roots[plane_id] is native and sketch.support_plane_id == public_plane.id
                    and sketch.attributes["native_object_id"] == NativeNodeId(profile),
                    "target public sketch does not use the actual source support correspondence")
        result[expectation["source_id"]] = public_plane.id
    return result


def target_read(data):
    payload = b64decode(data["candidate_b64"], validate=True)
    require(digest(payload) == data["artifact"]["sha256"], "generated bytes changed before strict read")
    source = data["source"]
    prewarm()
    with guarded():
        document = open_document(payload, source_format=FORMAT)
        archive = SldprtArchive.from_bytes(payload)
        link = ReadNativeLink(archive, 0)
        roots = IndexFeatures(link)
        boss, = (row for row in roots.values() if row.ClassValue.NameValue == "moExtrusion_c")
        owner = ReadExtrude(link, boss, roots)
        profile = owner.ProfileValue
        frame = ReadPrismFrame(profile, link.ConfigValue.RootValue, roots, FrontOnly=False)
        plane_id = profile.FieldsValue["pd_f78"].FieldsValue["ff0"]["f00"]
        support = roots[plane_id]
        require(ReadNativeName(support) == "Top Plane" and xyz(frame.z_axis) == (0, 1, 0)
                and owner.ParentsValue == (profile,) and owner.IsReversed and owner.ModeValue == "blind"
                and owner.SecondValue is None, "target reversed blind boss does not use its actual Top support")
        datums = target_datums(document, roots, profile, source, plane_id)
        origin_id = target_drivers(document, link, owner, source, profile.FieldsValue["pd_f80"])
        body, = document.bodies
        config, = document.configurations
        boss_id = NativeNodeId(boss)
        atom = ReadColdOutput(link)
        body_link = body.attributes["solidworks.authored_output_name"]
        require(atom is not None and atom.BossValue is boss and body.final_feature_id == f"sldprt:feature:{boss_id}"
                and atom.NameValue == body.name == source["body_name"]
                and body_link["atom_manager_id"] == atom.AtomValue.FieldsValue["f140"]
                and body_link["complete_brep_binding"] and body_link["native_kernel_identity"] is False
                and config.name == source["configuration"] and config.active,
                "target body and configuration lack the witnessed owners")
        solid, graph = box_incidence(document.brep, source["world_corners"], body.id)
        require(json.dumps(graph, sort_keys=True) == json.dumps(source["incidence"], sort_keys=True)
                and not document.brep_payloads and document.metadata["document_summary"] == data["projected_properties"]["summary"]
                and document.metadata["custom_properties"] == data["projected_properties"]["document"],
                "default strict target differs in shape incidence or literal properties")
        tree = [(row.name, str(row.kind), row.attributes["native_object_id"]) for row in document.feature_timeline]
        require(len(tree) == len(roots) and {row[2] for row in tree} == set(roots)
                and ReadNativeName(boss) == source["feature_name"]
                and ReadNativeName(profile) == source["feature_name"] + " Profile",
                "public target tree differs from the actual resolved construction")
        dims = [source["drivers"][name]["value_mm"] for name in DRIVERS]
        length, width, height = dims
        limits = body.topology
        corners = source["world_corners"]
        bounds = (xyz(limits.bounding_box.minimum), xyz(limits.bounding_box.maximum))
        expected = tuple(tuple(combine(point[i] for point in corners) for i in range(3)) for combine in (min, max))
        centre = tuple(sum(point[i] for point in corners) / len(corners) for i in range(3))
        require(isclose(limits.volume, length*width*height, rel_tol=1e-12)
                and isclose(limits.surface_area, 2*(length*width+length*height+width*height), rel_tol=1e-12)
                and all(isclose(a, b, rel_tol=0.0, abs_tol=1e-10)
                        for end, other in zip(bounds, expected, strict=True) for a, b in zip(end, other, strict=True)),
                "target measures differ from the authored source dimensions")
        return {
            "feature_tree": tree, "origin_feature_id": origin_id, "plane_feature_id": plane_id,
            "profile_feature_id": NativeNodeId(profile), "boss_feature_id": boss_id, "body_id": body.id,
            "body_boundary_id": solid, "body_atom_manager_id": body_link["atom_manager_id"],
            "datum_owners": datums, "bounds_mm": bounds, "centre_mm": centre,
            "driver_owners": source["drivers"], "volume_mm3": limits.volume, "area_mm2": limits.surface_area,
            "incidence_matches_all_source_shapes": True, "runtime_data_file_reads": 0,
        }


def isolate(mode, data):
    completed = subprocess.run([sys.executable, "-I", "-B", str(HERE), mode],
                               input=json.dumps(data, allow_nan=False), capture_output=True, text=True, timeout=120)
    require(completed.returncode == 0 and not completed.stderr, completed.stderr or "process failed")
    return json.loads(completed.stdout)


def main():
    if len(sys.argv) == 2 and sys.argv[1] in {"generate", "read"}:
        worker = generate if sys.argv[1] == "generate" else target_read
        print(json.dumps(worker(json.load(sys.stdin)), sort_keys=True, allow_nan=False))
        return
    parser = ArgumentParser()
    parser.add_argument("fcstd", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    base = ROOT / "re/solidworks/measurements/2026"
    native = json.loads(locked(base / "AttachedTopBoxGeneratedNative01.json", NATIVE_SHA))
    shared = json.loads(locked(base / "FreecadAttachedBoxSharedBuild01.json", SHARED_SHA))
    require(native["controls_healthy"] and native["distinct_native_processes"] == 8
            and native["oracle_file_version"] == "34.5.2.0604" and shared["native_baseline_sha256"] == NATIVE_SHA,
            "the prior matched native lifecycle changed")
    request = {"source": str(args.fcstd.resolve(strict=True)), "source_sha256": SOURCE_SHA, "locator": LOCATOR}
    generated = isolate("generate", request)
    require(generated == isolate("generate", request), "independent guarded builds produced different results")
    case = native["cases"][CASE]
    artifact = generated["artifact"]
    require(case["input_sha256"] == generated["source_sha256"] == SOURCE_SHA
            and artifact == {"bytes": case["bytes"], "sha256": case["output_sha256"], "streams": case["streams"]},
            "guarded result differs from the complete native-measured archive")
    readback = isolate("read", generated)
    require(readback == isolate("read", generated), "independent default strict reads produced different results")
    old = case["fresh_reopen_mass_si"]["Original"]
    require(isclose(readback["volume_mm3"] / 1e9, old["volume"], rel_tol=2e-7)
            and isclose(readback["area_mm2"] / 1e6, old["area"], rel_tol=2e-7)
            and all(isclose(a / 1000, b, rel_tol=2e-7, abs_tol=1e-12)
                    for a, b in zip(readback["centre_mm"], old["com"], strict=True)),
            "signed geometry differs from the exact prior native file")
    del generated["candidate_b64"]
    result = {"schema": "kit.sw2026.f14c-source-target-owner-proof.v1", "passed": True, **generated,
              "target": readback, "fresh_workers": {"build": 2, "read": 2},
              "prior_native_receipt_sha256": NATIVE_SHA, "prior_shared_receipt_sha256": SHARED_SHA,
              "analytic_comparison_tolerance_mm": 1e-10, "native_processes_started": 0,
              "same_native_locator": LOCATOR, "source_geometry_required_for_proof": True,
              "source_payload_carrier_emitted": False, "benchmark_conversion_credits": 0,
              "public_writer_qualified": False,
              "tools_sha256": {path.name: digest(path.read_bytes()) for path in (HERE, HERE.with_name("BoxIncidence.py"))}}
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")


if __name__ == "__main__":
    main()
