from argparse import ArgumentParser
from codecs import lookup
from contextlib import contextmanager
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from subprocess import check_output, run
from tarfile import open as open_tar
from tempfile import TemporaryDirectory
from xml.etree.ElementTree import fromstring
from zipfile import ZipFile
import json
import re
import sys


REVISION = "a1b26105b401a75edd32930847a96da45394a811"
MANIFEST = "e2053d84764ed9b65fc4bfe62f98b08c4d33bb57f096f3a4e9265e802e9288fa"
OBSERVATION = "0168290e4c7fe6bdba837ff27fe0d42b194927e76e00544cac9c2830f9246e53"
RECEIPTS = {
    "SdkFreecadBoxReleaseConstruction01": "9d7cc9d615fe8bd6fd9c3e10f1e3eca63fedec4e6638517a90a61f21f833173e",
    "SdkFreecadBoxReleaseNative01": "e87ae3d9520edcffd262b1dc2457b2bd4e5a70fe4ff34c1a1271079d5628b856",
}
BOUNDARY_TOOL = "re/tooling/sw2026/imported_body_source/AuditBakedFcstdSources.py"
BOUNDARY_TOOL_SHA256 = "be11b111d3ab377e35f45b3b83facc8eab299cb4efefbab0b3c4e4f302bc94ed"
CASES = {"recipe-1.0.2-F14a": "1.0.2", "recipe-1.1.4-F14a": "1.1.4"}
DIMENSIONS = ("Length", "Width", "Height")
SHAPES = {"Body": ("Shape",), "AdditiveBox": ("AddSubShape", "Shape", "SuppressedShape")}
MAP_NAME = "Body.Shape.Map.txt"
NATIVE_REFUSAL = "native-only feature definitions cannot be exported:"


def require(condition, detail):
    if not condition:
        raise ValueError(detail)


def digest(data):
    return sha256(data).hexdigest()


def wire(data):
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def checked(path, expected):
    require(path.is_file() and not path.is_symlink(), "expected one exact disclosed file")
    raw = path.read_bytes()
    require(digest(raw) == expected, "disclosed input digest differs")
    return raw


@contextmanager
def no_runtime_io():
    active = True
    attempts = []

    def audit(event, args):
        if active and (event in {"open", "os.scandir", "os.listdir", "os.mkdir", "os.rename", "os.remove",
                                 "os.system", "os.exec", "os.posix_spawn", "os.fork", "subprocess.Popen", "ctypes.dlopen"}
                       or event.startswith("socket.")
                       or (event == "import" and args[0].split(".")[0] in {"FreeCAD", "Part", "pythoncom", "win32com"})):
            attempts.append(event)
            raise PermissionError("model-only operation attempted " + event)

    sys.addaudithook(audit)
    try:
        yield
    finally:
        active = False
        require(not attempts, "guarded model operation attempted runtime I/O")


def element_map(raw, feature_id):
    lines = tuple(line.strip() for line in raw.decode("ascii").splitlines() if line.strip())
    require(len(lines) == 20 and lines[:7] == ("BeginElementMap v1", "1 PostfixCount 3", "Edge", "Face",
                                                   "Vertex", "MapCount 1", "ElementMap 1 1 3")
            and lines[-1] == "EndMap", "unqualified FreeCAD body element-map framing")
    prefix = f"{feature_id:x}"
    groups = {}
    for offset, kind in enumerate(("Edge", "Face", "Vertex")):
        label, child, values, names = lines[7 + offset * 4:11 + offset * 4]
        match = re.fullmatch(r"1 0 (\d+) (\d+) 0 ;:H([0-9a-f]+),([EFV]) 0", values)
        require(label == kind and child == "ChildCount 1" and names == "NameCount 0" and match is not None,
                "unqualified FreeCAD child element-map row")
        require(match.group(2, 3, 4) == (str(feature_id), prefix, kind[0]), "element map identifies another XML owner")
        groups[kind.casefold()] = {"child_count": 1, "local_name_count": 0, "member_count": int(match[1]),
                                   "child_xml_object_id": feature_id, "child_start_index": 1, "index_offset": 0,
                                   "child_map_index": 0, "string_id_count": 0}
    return groups


def source_archive(raw, document):
    from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.ReadBoxMat import ReadBoxMat

    with ZipFile(BytesIO(raw)) as zip_value:
        entries = {name: zip_value.read(name) for name in zip_value.namelist()}
        require(len(entries) == len(zip_value.namelist()), "source has duplicate archive members")
    expected = {"Document.xml", MAP_NAME} | {f"{owner}.{kind}.brp" for owner, kinds in SHAPES.items() for kind in kinds}
    require(set(entries) == expected, "source has a different presentation or geometry inventory")
    doc_xml = fromstring(entries["Document.xml"])
    ids = {node.get("name"): int(node.get("id")) for node in doc_xml.findall("./Objects/Object")}
    states = {node.get("name"): node.find("./Properties/Property[@name='Visibility']/Bool").get("value")
              for node in doc_xml.findall("./ObjectData/Object")}
    owners = {row["name"]: row["properties"] for row in document.metadata["freecad"]["objects"]}
    source_uid = doc_xml.find("./Properties/Property[@name='Uid']/Uuid").get("value")
    appearance_names = sorted({prop.get("name") for prop in doc_xml.findall(".//Property")
                               if any(token in prop.get("name", "").casefold() for token in
                                      ("appearance", "color", "display", "material", "texture", "transparency", "view", "visibility"))})
    require(set(ids) == set(states) == set(owners) and set(states.values()) == {"true"}
            and appearance_names == ["Material", "ShapeMaterial", "Visibility"], "source carries unqualified presentation state")
    require(doc_xml.find("./Properties/Property[@name='Material']/Map").get("count") == "0"
            and not document.materials and document.bodies[0].material_id is None, "source has separate material assignment")
    materials = {owner: ReadBoxMat(owners[owner]) for owner in SHAPES}
    for owner, kinds in SHAPES.items():
        for kind in kinds:
            require(owners[owner][kind]["children"][0]["attributes"]["file"] == f"{owner}.{kind}.brp",
                    "stored Shape member is not owned by its literal property")
    require(doc_xml.find("./ObjectData/Object[@name='Body']/Properties/Property[@name='Shape']/ElementMap2").get("file") == MAP_NAME,
            "Body.Shape lacks its linked element map")
    mapped = element_map(entries[MAP_NAME], ids["AdditiveBox"])
    return entries, {"source_uuid": source_uid, "object_ids": ids, "body_element_map": mapped,
                     "gui_document_present": False, "appearance_property_names": appearance_names,
                     "visibility_by_object": states, "default_shape_material_uuids": materials}


def source_payloads(document, raw, entries, physical):
    from AuditBakedFcstdSources import boundary_summary
    from convert.adapters.freecad.Native import DecodeAsciiBrep
    from interchange.document.Models.DocumentProvenance import IterProvenance

    signatures, boundaries = {}, {}
    body, = document.bodies
    feature, = document.feature_timeline
    for payload in document.brep_payloads:
        kind = payload.role.value
        sidecars = payload.attributes.get("freecad_sidecars", ())
        require(payload.id not in signatures and payload.provenance is not None
                and digest(payload.data) == payload.sha256, "native payload has lost its strict identity")
        signatures[payload.id] = {"member": payload.source_stream, "role": kind, "bytes": len(payload.data),
                                  "sha256": payload.sha256, "provenance_native_id": payload.provenance.native_id,
                                  "attribute_keys": sorted(payload.attributes), "sidecars": {}}
        for sidecar in sidecars:
            name = sidecar["source_stream"]
            require(name == MAP_NAME and payload.id == "freecad:brep:Body:Shape"
                    and sidecar["data"] == entries[name], "element-map bytes lost their actual Body.Shape owner")
            signatures[payload.id]["sidecars"][name] = {"bytes": len(entries[name]), "sha256": digest(entries[name])}
        if kind != "brep":
            expected = {"document": raw, "verification": bytes.fromhex(digest(raw))}[kind]
            require(payload.data == expected, "whole-document carrier or verification binding changed")
            if kind == "document":
                span, = payload.provenance.spans
                require((span.stream, span.offset, span.length, span.record_kind)
                        == ("Document.xml", 0, len(entries["Document.xml"]), "xml"), "whole-document XML provenance changed")
            continue
        require(payload.data == entries[payload.source_stream]
                and payload.attributes["freecad.native_document_sha256"] == digest(raw), "Shape carrier differs from source member")
        if payload.data:
            model = DecodeAsciiBrep(payload.data, id_prefix="source-shape", design_body_id=body.id)
            boundaries[payload.id] = boundary_summary(model, body.id)
        else:
            require(payload.id == "freecad:brep:AdditiveBox:SuppressedShape", "unexpected empty Shape carrier")
    attached = signatures["freecad:brep:Body:Shape"]["sidecars"]
    expected_counts = {"edge": len(document.brep.edges), "face": len(document.brep.faces), "vertex": len(document.brep.vertices)}
    require(len(signatures) == 6 and set(attached) == {MAP_NAME} and len(boundaries) == 3
            and {kind: row["member_count"] for kind, row in physical["body_element_map"].items()} == expected_counts,
            "body element map count disagrees with the full strict B-rep")
    strict_boundary = boundary_summary(document.brep, body.id)
    source_solid, = document.brep.bodies
    shape_refs = {row.id: row.attributes for row in document.brep_payloads if row.role.value == "brep"}
    require(shape_refs["freecad:brep:Body:Shape"]["body_id"] == body.id
            and shape_refs["freecad:brep:AdditiveBox:Shape"]["feature_id"] == feature.id
            and body.final_feature_id == feature.id
            and source_solid.attributes["brep_payload_id"] == "freecad:brep:Body:Shape"
            and source_solid.attributes["feature_id"] == feature.id,
            "Body.Shape B-rep no longer resolves to the actual source body and primitive")
    expected_geometry = {key: value for key, value in strict_boundary.items() if key not in {"body_id", "attribute_entity_counts"}}
    require(all(all(row[key] == value for key, value in expected_geometry.items()) for row in boundaries.values()),
            "nonempty source Shape carriers disagree with the complete strict box boundary")
    return {"payloads": signatures, "shape_carrier_boundaries": boundaries, "strict_body_boundary": strict_boundary,
            "body_shape_owner": {"body_id": body.id, "feature_id": feature.id, **source_solid.attributes},
            "record_provenance_native_ids": sorted(provenance.native_id for provenance in IterProvenance(document)),
            "source_attribute_keys": sorted(document.source.attributes), "source_metadata_keys": sorted(document.metadata),
            "freecad_metadata_keys": sorted(document.metadata["freecad"])}


def refused(operation, expected, diagnostic, source_path):
    try:
        operation()
    except expected as error:
        message = str(error).replace(str(source_path), "<disclosed source>")
        require(diagnostic in message, "writer refusal happened at an unqualified boundary")
        return {"type": type(error).__name__, "diagnostic": message}
    raise ValueError("intact source reached an unqualified writer route")


def normal_write_boundaries(document, source, target):
    from convert import write_document
    from convert.adapters.base.WritePolicy import GetDocumentCaps
    from convert.adapters.registry.RegistryErrors import NotFoundError
    from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.ReadBoxSource import ReadBoxSource
    from convert.adapters.solidworks.Core.Preparation.PlanNativePart import PlanNativePart
    from convert.adapters.solidworks.Core.Preparation.PrepareNative import PrepareNative
    from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter

    writer = SldprtWriter()
    options = {"destination_format": writer.info.FormatId, "allow_carrier": False, "values": {"require_native_transfers": True}}
    stream = BytesIO(b"refusal must keep the destination unchanged")
    initial_stream, initial_cursor = stream.getvalue(), stream.tell()
    with no_runtime_io():
        rows = {
            "implicit_path": refused(lambda: write_document(document, target), NotFoundError, "no writer supports the destination", source),
            "native_only_path": refused(lambda: write_document(document, target, **options), ValueError, NATIVE_REFUSAL, source),
            "native_only_stream": refused(lambda: write_document(document, stream, **options), ValueError, NATIVE_REFUSAL, source),
            "direct_adapter": refused(lambda: writer.write(document, target), ValueError, NATIVE_REFUSAL, source),
            "full_preparer": refused(lambda: PrepareNative(document, target, 0), ValueError, "bare local import requires a neutral millimetre B-rep", source),
            "parametric_planner": refused(lambda: PlanNativePart(document), ValueError, "plain part preparation does not admit unresolved or extended source state", source),
            "attached_primitive_projector": refused(lambda: ReadBoxSource(document), ValueError, "FreeCAD primitive uses another attachment engine or owner", source),
        }
        require(not writer.supports(document, target), "unsupported intact source is selected by the writer")
    require(not any(target.parent.iterdir()) and (stream.getvalue(), stream.tell()) == (initial_stream, initial_cursor),
            "failed write touched a native destination")
    caps = GetDocumentCaps(document)
    missing = sorted(cap.value for cap in caps - writer.info.Capabilities)
    require(missing == ["native_payloads", "provenance", "roundtrip_metadata"], "writer capability gap differs")
    return {"writer_refusals": rows, "path_output_files": 0, "stream_unchanged": True,
            "inferred_source_capabilities": sorted(cap.value for cap in caps), "unsupported_capabilities": missing}


def compare_prior_neutral(actual, locked):
    from convert.adapters.freecad.Replay.NativeIdentity import KExplicitSketchProfile, KNativeDocId, KReplaySketchAttr
    from interchange.serialization.EncodeData import ToData

    current = ToData(actual)
    previous = locked["document"]
    current["source"]["path"] = previous["source"]["path"] = "<disclosed source>"
    old, = (row for row in previous["brep_payloads"]["$tuple"] if row["id"] == KNativeDocId)
    require(KReplaySketchAttr not in old["attributes"], "original neutral request already contains the newer profile")
    old["attributes"][KReplaySketchAttr] = KExplicitSketchProfile
    require(current == previous, "full strict source differs beyond its documented replay profile and locator")
    return {"strict_source_model_sha256_without_locator": digest(wire(current)),
            "earlier_neutral_difference": {"payload_id": KNativeDocId, "added_attribute": KReplaySketchAttr,
                                           "value": KExplicitSketchProfile}}


def model_only_target(document, target_locator, native, release, physical):
    from AuditFreecadBoxReleases import read_box
    from ProjectFreecadBox import project
    from convert import open_document
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.Preparation.FreecadBox.MakeOriginBoxPart import MakeOriginBoxPart
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

    with no_runtime_io():
        projected = project(document, source_labels=True)
        candidate = MakeOriginBoxPart(projected.model, target_locator, projected.creation_epoch,
                                      projected.properties, UnitsValue=projected.unit_recipe)
    prior = native["generated"]
    require(digest(candidate.BytesValue) == prior["file_sha256"], "current model-only part is not the measured native input")
    archive = SldprtArchive.from_bytes(candidate.BytesValue)
    exact_streams = prior["exact_critical_streams"] | prior["exact_version_metadata"]
    require(len(exact_streams) == 10 and all(expected["byte_identity"] and digest(archive.require(name)) == expected["sha256"]
                                              and len(archive.require(name)) == expected["bytes"] for name, expected in exact_streams.items()),
            "current model-only part differs from the prior native receipt")
    target = open_document(candidate.BytesValue, source_format="solidworks.sldprt")
    target.assert_valid()
    source_parameters = {row.attributes["freecad_path"]: row for row in document.parameters}
    target_parameters = {row.name: row for row in target.parameters}
    sketch, = target.sketches
    boss, = (row for row in target.feature_timeline if row.kind.value == "extrusion")
    anchors = {row.parameter_id for row in sketch.constraints if row.kind == "distance"}
    require(set(target_parameters) == set(DIMENSIONS) and set(sketch.parameter_ids) == anchors
            == {target_parameters[name].id for name in DIMENSIONS[:2]}
            and boss.parameter_ids == (target_parameters["Height"].id,) and boss.definition.length == target_parameters["Height"].value,
            "native geometry does not bind the three independent source dimensions")
    for name in DIMENSIONS:
        origin, lowered = source_parameters[name], target_parameters[name]
        require(lowered.role == origin.role and lowered.value == origin.value
                and lowered.owner_id == (boss.id if name == "Height" else "sldprt:feature:" + sketch.id.rsplit(":", 1)[1])
                and projected.parameter_bindings[origin.id] == name + "@" + (boss.name if name == "Height" else sketch.name),
                "target dimension changed the actual source owner or units")
    body, = target.bodies
    geo, = target.brep.bodies
    require(body.final_feature_id == boss.id and geo.design_body_id == body.id and not boss.suppressed
            and not target.materials and body.material_id is None, "derived solid or material state changed")
    text = target.metadata["custom_properties"]
    require(text["FreeCAD Uid"] == physical["source_uuid"] and all(
        text[f"FreeCAD {caption} Material UUID"] == physical["default_shape_material_uuids"][owner]
        for caption, owner in (("Body", "Body"), ("Feature", "AdditiveBox"))
    ), "literal source UUID or material owner differs in the target text")
    part_fields = ReadNativeLink(archive, 0).ConfigValue.RootValue.FieldsValue
    visual_values = part_fields["f78"].FieldsValue
    material_name = visual_values["f20"]["f20"]
    dense_values = {row["effective_density_kg_per_m3"] for row in native["native_mass_measurements"]}
    require(part_fields["f1420"] is None and material_name == "" and dense_values == {1.0},
            "prior unassigned effective density is not the current unassigned material profile")
    build = {"source_text": {"file": projected.properties.DocumentFields, "summary": projected.properties.SummaryFields},
             "source_body_label": projected.source_body_label, "source_dimensions_mm": projected.dimensions_mm}
    typed = read_box(candidate.BytesValue, build, release)
    return {
        "full_native_measured_byte_match": True, "generated_sha256": prior["file_sha256"],
        "generated_bytes": len(candidate.BytesValue), "original_logical_destination": target_locator,
        "live_driver_bindings": {name: {"source_id": source_parameters[name].id,
                                       "target_id": row.id, "target_owner_id": row.owner_id,
                                       "native_name": projected.parameter_bindings[source_parameters[name].id],
                                       "millimeters": row.value.value} for name, row in target_parameters.items()},
        "other_source_scalars": {name: {"id": row.id, "neutral_role": row.role.value, "value": row.value.value,
                                      "kind": row.value.kind.value, "owner_id": row.owner_id}
                                 for name, row in source_parameters.items() if name not in DIMENSIONS},
        "body_id": body.id, "boss_id": boss.id, "origin_sketch_plane_id": sketch.support_plane_id,
        "typed_read": typed, "literal_text_property_names": sorted(projected.properties.DocumentFields),
        "target_material_pointer_present": False, "target_visual_material_id_name": material_name,
        "target_default_visual_fields": {name: visual_values[name] for name in ("f0c", "f14", "f18", "has88")},
        "prior_unassigned_native_effective_density_kg_per_m3": next(iter(dense_values)),
        "native_tested_streams": sorted(exact_streams),
        "target_geometry_tolerances_mm": {name: sorted(set(row.tolerance for row in getattr(target.brep, name)), key=str)
                                           for name in ("vertices", "edges", "faces")},
        "target_source_freecad_payloads": sum(row.format_id.startswith("freecad.fcstd") for row in target.brep_payloads),
        "runtime_input_reads": 0,
    }


def measure(sdk, request):
    sys.path[:0] = [str(sdk / "src"), str(sdk / "rules"), str(Path(__file__).parent / "imported_body_source")]
    from convert import open_document
    from interchange.serialization.EncodeData import ToData

    for name in ("ascii", "latin-1", "utf-8", "utf-16-le"):
        lookup(name)
    source = Path(request["original"])
    raw = checked(source, request["original_sha256"])
    document = open_document(source, strict=True, include_brep=True, include_tessellation=True)
    document.assert_valid()
    require(document.source.sha256 == digest(raw) and document.source.path == str(source), "strict source identity was changed")
    before = digest(wire(ToData(document)))
    entries, physical = source_archive(raw, document)
    payloads = source_payloads(document, raw, entries, physical)
    neutral = compare_prior_neutral(document, request["locked"])
    with TemporaryDirectory(prefix="kit-f14a-refusal-") as scratch:
        refusal = normal_write_boundaries(document, source, Path(scratch) / "F14a.SLDPRT")
    target = model_only_target(document, request["locked"]["native_path"], request["native"], request["release"], physical)
    require(digest(wire(ToData(document))) == before and checked(source, digest(raw)) == raw,
            "whole-source probe changed the source document or payloads")
    return {"physical": physical, "retained_owners": payloads, "strict_native_source_unchanged": True,
            "original_sha256": digest(raw), **neutral, **refusal, "generated_projection": target}


def main(observations, fixtures):
    root = Path(__file__).resolve().parents[3]
    inputs = json.loads(checked(observations / "Inputs.json", MANIFEST))
    observed = json.loads(checked(observations / "Result.json", OBSERVATION))
    require(inputs["heldout_inputs"] == 0 and not inputs["original_corpus_membership_verified"], "input lock leaves scope")
    receipts = {name: json.loads(checked(root / f"re/solidworks/measurements/2026/{name}.json", wanted))
                for name, wanted in RECEIPTS.items()}
    native = receipts["SdkFreecadBoxReleaseNative01"]
    builds = receipts["SdkFreecadBoxReleaseConstruction01"]
    require(native["scoped_native_lifecycle_passed"] and len(native["healthy_control_records_sha256"]) == 2
            and native["independent_successful_driver_edits"] == 6 and not native["heldout_inputs_read"]
            and native["frozen_guarded_build_sha256"] == builds["raw_sha256"]["guarded_replay"]
            and builds["raw_sha256"]["source_observation"] == OBSERVATION, "prior native or analytic evidence differs")
    checked(root / BOUNDARY_TOOL, BOUNDARY_TOOL_SHA256)
    frozen = {BOUNDARY_TOOL: BOUNDARY_TOOL_SHA256}
    cases = {}
    with TemporaryDirectory(prefix="kit-f14a-sdk-") as isolated:
        sdk = Path(isolated)
        archive = check_output(("git", "-C", str(root), "archive", "--format=tar", REVISION, "src"))
        with open_tar(fileobj=BytesIO(archive)) as source:
            source.extractall(sdk, filter="data")
        rules = sdk / "rules"
        rules.mkdir()
        for name in ("ProjectFreecadBox", "FreecadBoxRelease", "AuditFreecadBoxReleases"):
            path = f"re/tooling/sw2026/{name}.py"
            data = check_output(("git", "-C", str(root), "show", f"{REVISION}:{path}"))
            (rules / f"{name}.py").write_bytes(data)
            frozen[path] = digest(data)
        for key, release in CASES.items():
            stock, = (row for row in inputs["inputs"] if row["case"] == key)
            observed_row, = (row for row in observed["rows"] if row["case"] == key)
            native_row, = (row for row in native["cases"] if row["source_release"] == release)
            build = builds["builds"][key]
            wanted = stock["sha256"]
            require(wanted == build["source_sha256"] == native_row["source_freecad_sha256"] == observed_row["sha256"]
                    and build["output_sha256"] == native_row["generated"]["file_sha256"], "source or generated identity differs")
            locked_sha = observed_row["strict_request_sha256"]
            require(build["input_strict_sha256"] == locked_sha, "strict source request lock differs")
            locked = json.loads(checked(observations / "Neutral" / f"{key}.json", locked_sha))
            original = fixtures / f"{key}.FCStd"
            require(locked["document"]["source"]["sha256"] == wanted and locked["preserve_source_labels"] is True,
                    "original neutral source is not the native-tested label profile")
            request = {"original": str(original), "original_sha256": wanted, "locked": locked, "native": native_row, "release": release}
            captures = []
            for _ in range(2):
                result = run((sys.executable, "-I", "-B", __file__, "--worker", isolated), input=wire(request),
                             capture_output=True, cwd=sdk, timeout=120)
                require(result.returncode == 0 and not result.stderr, result.stderr.decode(errors="replace"))
                captures.append(json.loads(result.stdout))
            require(captures[0] == captures[1], "independent intact-source probes differ")
            cases[key] = {"locked_request_sha256": locked_sha, **captures[0]}
    return {"schema": "kit.sw2026.freecad-f14a-intact-source-boundary.v1", "sdk_revision": REVISION,
            "prior_source_manifest_sha256": MANIFEST, "prior_source_observation_sha256": OBSERVATION,
            "prior_receipts_sha256": RECEIPTS, "projection_tool_sha256": frozen,
            "independent_processes": 4, "heldout_sources_read": 0, "completed_corpus_conversions": 0,
            "public_writer_qualified": False, "native_processes_started": 0, "cases": cases}


if __name__ == "__main__":
    if sys.argv[1:2] == ["--worker"]:
        result = measure(Path(sys.argv[2]), json.load(sys.stdin))
    else:
        parser = ArgumentParser(description="Audit two checksum-bound disclosed origin AdditiveBox documents")
        parser.add_argument("observations", type=Path)
        parser.add_argument("disclosed_fixtures", type=Path)
        args = parser.parse_args()
        result = main(args.observations.resolve(strict=True), args.disclosed_fixtures.resolve(strict=True))
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False))
