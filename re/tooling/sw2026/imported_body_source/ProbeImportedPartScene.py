from argparse import ArgumentParser
from codecs import lookup
from dataclasses import asdict, replace
from hashlib import sha256
import json
from math import isclose
import os
from pathlib import Path, PureWindowsPath
import re
from shutil import copyfile
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[4]
RESEARCH = Path("re/tooling/sw2026")
TOOLS = RESEARCH / "imported_body_source"
IMPORTS = Path("src/convert/adapters/solidworks/Archive/Construction/Part/Imports")
PROPERTIES = IMPORTS.parents[1] / "Metadata/Properties"
sys.path[:0] = [str(ROOT / "src"), str(ROOT), str(ROOT / TOOLS), str(ROOT / RESEARCH), str(ROOT / RESEARCH / "serial")]

from AuthorCurves import EvidenceFailure, digest, require, write_json
from AuthorRectangleAnchors import CONTROL, ORACLE, control
from BuildImportedLocalPart import EPOCH, verify_part
from EvaluateSealedImportedGeometry import expected_shape
from LocalBodyKernel import fingerprint
from ObserveLocalImportedPart import phase
from ProjectDisclosedImport import decode_import, project_import, rectangular_boundary
from ProjectImportedSemantics import project_import_semantics, project_part_text, read_empty_file_owner
from RunImportedBodySources import cases
from StageLocalPartProbe import pinned_tree
from VerifyBareImportPackage import BareLabels, EXPECTED_LIGHT_STREAMS, guard_build, recipe
from convert.adapters.solidworks.Archive.Construction.Part.Imports.MakeBareImport import MakeBareImport
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Members.ReadLightInput import ReadLightInput
from downstream.lighting.AuditStockPartLights import actual_scene
from interchange import CadDocument
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordSource import CadSource


SCHEMA = "kit.sw2026.imported-native-scene-probe.v1"
INPUTS = {
    "Disclosed": ("ImportedBodySourceDisclosed03/DisclosedImported.SLDPRT", "13f1ef12ab727323a826ead989087079f44e9b24a4326aa9b65be61c9d81f325"),
    "OtherShape": ("ImportedBodyContrast02/OtherShape.SLDPRT", "8c77ddcd2451466781ae153b7724808f4e9bbf102ebd14aab6cd6b9274870f1d"),
    "RenamedFeature": ("ImportedBodyContrast02/RenamedFeature.SLDPRT", "660277a250a8c719705d6332cfc1f3713ccc5082d07de2ad5c3006279c1f20e8"),
}
BOUND_OPERATORS = tuple(path.as_posix() for path in (
    *(TOOLS / name for name in ("ProbeImportedPartScene.py", "ObserveLocalImportedPart.py", "ProjectDisclosedImport.py", "ProjectImportedSemantics.py")),
    *(RESEARCH / name for name in ("AuthorCurves.py", "AuthorRectangleAnchors.py", "OracleIdentity.py", "Swapp.py", "downstream/lighting/AuditStockPartLights.py")),
    *(IMPORTS / name for name in ("BindImportScene.py", "CheckBareImport.py", "MakeBareImport.py", "ReadImportScene.py")),
    *(PROPERTIES / name for name in ("MakePartProps.py", "PartTextInput.py")),
))


def light_scene(raw):
    nodes, _ = actual_scene(SldprtArchive.from_bytes(raw), "moBaseBody_c")
    folder, *members = nodes
    require(folder.FieldsValue["f60"]["tail"] == 0, "unprojected environment member tail")
    return ReadNodeName(folder), tuple(map(ReadLightInput, members))


def decoded_scene_row(folder, lights):
    types = {"ambient": "AmbientLight", "directional": "DirectionLight"}
    return tuple((light.NameValue, types[light.KindValue], folder) for light in lights)


def prepared_part(source, target, preserve_empty=False, *, preserve_empty_file_owner=False):
    original = decode_import(source)
    footprint = project_import(original)
    semantics = project_import_semantics(original)
    folder, lights = light_scene(source)
    require(not semantics.body_name_is_authored, "light trial expects a derived body label")
    require(not any((semantics.properties.SummaryFields, semantics.properties.DocumentFields,
                     semantics.properties.ConfigurationFields)), "light trial expects empty source property values")
    document = CadDocument(CadSource("kit.neutral", "", ""),
                           (Configuration("active", semantics.configuration_name, True),), (), (), (), (), (), (),
                           brep=footprint.model)
    labels = BareLabels(target.stem, semantics.configuration_name, semantics.feature_name)
    properties = project_part_text(original, preserve_empty=True) if preserve_empty else semantics.properties
    manager_stream = None
    if preserve_empty_file_owner:
        require(preserve_empty, "property owner trial preserves the source XML scopes")
        manager_stream = read_empty_file_owner(source)
        properties = replace(properties, HasEmptyFileOwner=True)
    settings = recipe(labels, target, EPOCH, properties)
    property_streams = []
    with guard_build() as audit:
        candidate = MakeBareImport(document, settings, labels, LightValues=lights)
        empty = MakeBareImport(document, settings, labels)
        details = verify_part(candidate.BytesValue, candidate.StreamsValue)
        require(light_scene(candidate.BytesValue) == (folder, lights), "generated part changed an authored light value")
        decoded = decode_import(candidate.BytesValue)
        feature, = (row for row in decoded.feature_timeline if row.kind == "imported")
        active, = decoded.configurations
        body, = decoded.bodies
        actual = rectangular_boundary(decoded.brep, body.id).limits
        expected = rectangular_boundary(footprint.model).limits
        require(feature.name == semantics.feature_name and body.final_feature_id == feature.id
                and body.name == semantics.body_name and active.name == semantics.configuration_name
                and all(isclose(coordinate, point, rel_tol=0, abs_tol=1e-9)
                        for values, bound in zip(actual, expected, strict=True)
                        for coordinate, point in zip(values, bound, strict=True)),
                "generated part changed local boundary or typed source labels")
        if preserve_empty:
            require(properties.EmptyScopes == {"summary", "document", "configuration"}
                    and project_part_text(decoded, preserve_empty=True) == replace(properties, HasEmptyFileOwner=False),
                    "generated read did not recover all three explicit empty scopes")
            no_text = MakeBareImport(document, recipe(labels, target, EPOCH, semantics.properties), labels, LightValues=lights)
            property_streams = sorted(name for name in candidate.StreamsValue.keys() | no_text.StreamsValue.keys()
                                      if candidate.StreamsValue.get(name) != no_text.StreamsValue.get(name))
            expected = {"docProps/core.xml", "docProps/custom.xml", "docProps/Config-0-Properties.xml"}
            if preserve_empty_file_owner:
                expected.add("Contents/CusProps")
            require(set(property_streams) == expected, "explicit property owners changed unrelated streams")
        if preserve_empty_file_owner:
            without_owner = replace(settings, PropertiesValue=replace(properties, HasEmptyFileOwner=False))
            control = MakeBareImport(document, without_owner, labels, LightValues=lights)
            unrelated = {name: value for name, value in candidate.StreamsValue.items() if name != "Contents/CusProps"}
            require(unrelated == control.StreamsValue and read_empty_file_owner(candidate.BytesValue) == manager_stream,
                    "modeled file property owner differs from its native layout or changed other streams")
    contrast = sorted(name for name in candidate.StreamsValue.keys() | empty.StreamsValue.keys()
                      if candidate.StreamsValue.get(name) != empty.StreamsValue.get(name))
    require(set(contrast) == EXPECTED_LIGHT_STREAMS, "authored lights changed unrelated native state")
    result = {
        "file": fingerprint(candidate.BytesValue), "feature": details["feature"],
        "neutral_lights": tuple(map(asdict, lights)), "native_scene": decoded_scene_row(folder, lights),
        "stream_count": len(candidate.StreamsValue), "same_path_empty_contrast": contrast,
        "empty_property_streams": property_streams,
        "explicit_empty_text_owners_preserved": "solidworks.part_text_properties" in decoded.metadata,
        "runtime_file_reads": len(audit.DeniedReads), "native_path": str(target),
    }
    if preserve_empty_file_owner:
        result["file_property_owner"] = fingerprint(candidate.StreamsValue["Contents/CusProps"])
    return candidate.BytesValue, result


def read_checked(path, expected):
    value = path.read_bytes()
    require(sha256(value).hexdigest() == expected, f"locked hash differs for {path.name}")
    return value


def emit(packet, guest, publish, preserve_empty):
    require(os.name != "nt", "prepare disclosed part candidates on the host")
    for codec in ("ascii", "latin-1", "utf-8", "utf-16-le"):
        lookup(codec)
    if publish:
        (packet / "Candidates").mkdir()
    result = {}
    for name, (_, checksum) in INPUTS.items():
        path = packet / "Sources" / (name + ".SLDPRT")
        target = guest / "Generated" / path.name
        data, report = prepared_part(read_checked(path, checksum), target, preserve_empty)
        require(digest(path) == checksum, "disclosed source changed while preparing")
        if publish:
            with (packet / "Candidates" / path.name).open("xb") as output:
                output.write(data)
        result[name] = report | {"source_sha256": checksum}
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


def prepare(source_root, packet, guest, revision, preserve_empty):
    require(re.fullmatch(r"[a-f0-9]{40}", revision) and len(guest.parts) == 2 and guest.drive.casefold() == "c:"
            and re.fullmatch(r"KitImportScene[0-9]{2}", guest.name), "use a committed revision and fresh guest directory")
    require(not packet.is_relative_to(ROOT), "keep the disclosed staging packet outside Kit")
    packet.mkdir()
    (packet / "Sources").mkdir()
    for name, (relative, checksum) in INPUTS.items():
        (packet / "Sources" / (name + ".SLDPRT")).write_bytes(read_checked(source_root / relative, checksum))
    control_path = source_root / "ImportedBodySourceDisclosed03/Control.SLDPRT"
    (packet / "Control.SLDPRT").write_bytes(read_checked(control_path, CONTROL))
    directory = packet / "Code"
    pinned_tree(ROOT, revision, directory)
    entry = directory / TOOLS / Path(__file__).name
    argv = [sys.executable, "-I", "-B", str(entry), "emit", str(packet), str(guest)]
    if preserve_empty:
        argv.append("--preserve-empty-text")
    clean = subprocess.check_output(argv)
    repeat = subprocess.check_output([*argv, "--publish"])
    require(clean == repeat, "two frozen scene builds differ")
    (packet / "Build.json").write_bytes(clean)
    job = packet / "Job.json"
    write_json(job, {"schema": SCHEMA, "revision": revision, "guest": str(guest), "oracle_sha256": ORACLE,
                     "build_sha256": digest(packet / "Build.json"),
                     "operator_hashes": {name: digest(directory / name) for name in BOUND_OPERATORS}})
    print(json.dumps({"job_sha256": digest(job), "revision": revision, "builds": len(INPUTS)}))


def compare(actual, wanted):
    if type(wanted) is float:
        return type(actual) is float and isclose(actual, wanted, rel_tol=2e-13, abs_tol=1e-13)
    if isinstance(wanted, (tuple, list)):
        return isinstance(actual, (tuple, list)) and len(actual) == len(wanted) and all(
            compare(value, witness) for value, witness in zip(actual, wanted, strict=True))
    if isinstance(wanted, dict):
        return isinstance(actual, dict) and actual.keys() == wanted.keys() and all(compare(actual[key], wanted[key]) for key in wanted)
    return type(actual) is type(wanted) and actual == wanted


def measure_case(packet, guest, name, build, record, row):
    filename = name + ".SLDPRT"
    source, generated, saved = tuple(guest / branch / filename for branch in ("Sources", "Generated", "Saved"))
    require(build["source_sha256"] == INPUTS[name][1] and generated == Path(build["native_path"])
            and build["runtime_file_reads"] == 0, "native candidate is not the guarded pinned build")
    source.write_bytes(read_checked(packet / "Sources" / filename, build["source_sha256"]))
    generated.write_bytes(read_checked(packet / "Candidates" / filename, build["file"]["sha256"]))
    shape = expected_shape(cases("disclosed" if name == "Disclosed" else "contrast")[name])
    scene = tuple(map(tuple, build["native_scene"]))
    baseline = record(name + "Source", phase, source, build["source_sha256"], shape, build["feature"], scene=scene)
    if not baseline["passed"]:
        return
    first = record(name + "Generated", phase, generated, build["file"]["sha256"], shape, build["feature"], save=saved, scene=scene)
    if not first["passed"]:
        return
    reopened = record(name + "Reopen", phase, saved, first["saved_sha256"], shape, build["feature"],
                      reference=first["rebuilt"]["persistent_reference"], scene=scene)
    if not reopened["passed"]:
        return
    folder, lights = light_scene(read_checked(saved, first["saved_sha256"]))
    require(decoded_scene_row(folder, lights) == scene and compare(tuple(map(asdict, lights)), build["neutral_lights"]),
            "native save changed an authored light value")
    if build["explicit_empty_text_owners_preserved"]:
        original = project_part_text(decode_import(read_checked(source, build["source_sha256"])), preserve_empty=True)
        saved_text = project_part_text(decode_import(read_checked(saved, first["saved_sha256"])), preserve_empty=True)
        require(saved_text == original, "native save changed an explicit empty property scope")
        row["saved_empty_text_scopes"] = sorted(saved_text.EmptyScopes)
    row.update(binary_light_values_preserved=sum(len(asdict(light)) for light in lights), full_disclosed_lifecycle=True)


def observe(job_path, checksum):
    require(os.name == "nt", "run the COM observation only in Windows")
    packet = job_path.parent
    job = json.loads(read_checked(job_path, checksum))
    require(ROOT == packet / "Code" and job["schema"] == SCHEMA and job["oracle_sha256"] == ORACLE
            and set(job["operator_hashes"]) == set(BOUND_OPERATORS)
            and all(digest(ROOT / name) == value for name, value in job["operator_hashes"].items()),
            "disclosed scene job differs from its frozen operator closure")
    cases_value = json.loads(read_checked(packet / "Build.json", job["build_sha256"]))
    require(set(cases_value) == set(INPUTS), "disclosed scene cases were changed")
    guest = Path(job["guest"])
    require(guest.parent == Path("C:\\") and re.fullmatch(r"KitImportScene[0-9]{2}", guest.name), "invalid guest receipt path")
    guest.mkdir()
    for name in ("Sources", "Generated", "Saved"):
        (guest / name).mkdir()
    control_path = guest / "Control.SLDPRT"
    control_path.write_bytes(read_checked(packet / control_path.name, CONTROL))
    result_path = packet / "Native.json"
    require(not result_path.exists(), "this job already published a receipt")
    result = {"schema": SCHEMA, "job_sha256": checksum, "writer_revision": job["revision"], "oracle_sha256": ORACLE,
              "native_version": "34.5.2.0604", "scoped_lifecycles": 0, "heldout_cases": 0,
              "whole_source_admitted": False, "observations": {}, "cases": {}}

    def record(label, operation, *args, **options):
        row = operation(guest, label, *args, **options)
        result["observations"][label] = row
        write_json(result_path, result)
        print(json.dumps({"phase": label, "passed": row["passed"], "open": row.get("open"),
                          "first_failure": row.get("first_failure"), "cold_failure": row.get("cold_failure")}), flush=True)
        return row

    before = record("ControlBefore", control, control_path)
    try:
        if before["passed"]:
            for name, build in cases_value.items():
                row = {"binary_light_values_preserved": 0, "full_disclosed_lifecycle": False}
                result["cases"][name] = row
                try:
                    measure_case(packet, guest, name, build, record, row)
                except (EvidenceFailure, KeyError, OSError, TypeError, ValueError) as error:
                    row["case_error"] = str(error)
    finally:
        after = record("ControlAfter", control, control_path)
    processes = {tuple(row["oracle_identity"][key] for key in ("process_id", "process_creation_filetime"))
                 for row in result["observations"].values() if row.get("oracle_identity")}
    result["controls_healthy"] = bool(before["passed"] and after["passed"] and len(processes) == len(result["observations"]))
    result["distinct_native_processes"] = len(processes)
    result["scoped_lifecycles"] = sum(row["full_disclosed_lifecycle"] for row in result["cases"].values()) if result["controls_healthy"] else 0
    write_json(result_path, result)
    print(json.dumps({key: result[key] for key in ("scoped_lifecycles", "controls_healthy", "distinct_native_processes")}))
    return int(result["scoped_lifecycles"] != len(INPUTS))


if __name__ == "__main__":
    parser = ArgumentParser(description="Freeze and measure disclosed model-only part lighting round trips")
    modes = parser.add_subparsers(dest="mode", required=True)
    prep = modes.add_parser("prepare")
    prep.add_argument("source_root", type=Path)
    prep.add_argument("packet", type=Path)
    prep.add_argument("guest", type=PureWindowsPath)
    prep.add_argument("--revision", required=True)
    prep.add_argument("--preserve-empty-text", action="store_true")
    own = modes.add_parser("emit")
    own.add_argument("packet", type=Path)
    own.add_argument("guest", type=PureWindowsPath)
    own.add_argument("--publish", action="store_true")
    own.add_argument("--preserve-empty-text", action="store_true")
    oracle = modes.add_parser("observe")
    oracle.add_argument("job", type=Path)
    oracle.add_argument("--job-sha256", required=True)
    args = parser.parse_args()
    if args.mode == "prepare":
        prepare(args.source_root.resolve(), args.packet.resolve(), args.guest, args.revision, args.preserve_empty_text)
    elif args.mode == "emit":
        emit(args.packet.resolve(), args.guest, args.publish, args.preserve_empty_text)
    else:
        raise SystemExit(observe(args.job.resolve(), args.job_sha256))
