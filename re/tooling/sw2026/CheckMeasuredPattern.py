from argparse import ArgumentParser
from codecs import lookup
from contextlib import contextmanager
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from io import BytesIO
import json
from math import isclose
from os import getpid
from pathlib import Path, PureWindowsPath
import sys
from tempfile import TemporaryDirectory
from zlib import ZLIB_RUNTIME_VERSION


HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
FIXTURES = Path("re/solidworks/v2026/corpus/linear-pattern/MeasuredCold01")
ALTERNATE = Path("re/solidworks/v2026/corpus/linear-pattern/MeasuredZlibNg01")
FORMAT = "solidworks.sldprt"
MEASUREMENT = "solidworks_native_measurement"
PRESENTATION = "solidworks_pattern_presentation"
SOURCE_HASHES = {
    "ColdRaisedPatternA": "f7e5290dfda2cd2aedfc281ea8ee6275fd1214fc011bcda51f88d43d8cc4356f",
    "ColdRaisedPatternB": "032c9c5696a4b97a9a5c5178147cb8443b90a6350588154dec693ff56d372754",
}
PACKET_SHA = "da60bbfdc5411448b9aa5cd06c2a8772a0e0f2c39efa14ba2dc336c625e32cb1"
RESULT_SHA = "ae4f5853e4066a0d3f00cf4cbdaac12797b18c55c268ada6431d7e062bd5d23b"
ALTERNATE_HASHES = {
    "ColdRaisedPatternA": "60f2289933b6fa60bf601521d616c0616e6b56581eda95333e27f0d5092646a5",
    "ColdRaisedPatternB": "d47491db20319c0851c2960b3f9ae0f733ffd7ecf0de5c99ab715a881e375c2b",
}
ALTERNATE_PACKET_SHA = "9e8456c5f266646e7a96ffa711c5a4e3be957ffa807eaddc4e9aa8e0dae8bf8c"
ALTERNATE_RESULT_SHA = "c119cfd3f1faef104030333cab7c55221f890ea52dc3a853b115e8e4108ec0c4"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(value):
    return sha256(value).hexdigest()


def read_bound_receipt(fixture, packet_sha, result_sha):
    packet = (fixture / "Packet.json").read_bytes()
    observed = json.loads((fixture / "Result.json").read_bytes())
    result = (json.dumps(observed, indent=2) + "\n").replace("\n", "\r\n").encode("utf-8")
    require(digest(packet) == packet_sha and digest(result) == result_sha,
            "disclosed native packet or terminal report changed")
    return packet, result


def read_inputs(root, name, alternate=False):
    fixture = root / FIXTURES
    packet_sha, result_sha, source_hashes = PACKET_SHA, RESULT_SHA, SOURCE_HASHES
    evidence_dir = fixture
    if alternate:
        evidence_dir = root / ALTERNATE
        packet_sha, result_sha = ALTERNATE_PACKET_SHA, ALTERNATE_RESULT_SHA
        source_hashes = ALTERNATE_HASHES
    packet, result = read_bound_receipt(evidence_dir, packet_sha, result_sha)
    request = (fixture / f"{name}Request.json").read_bytes()
    streams = json.loads((fixture / "Streams.json").read_bytes())
    cases = json.loads(packet)["files"]
    report = json.loads(result)
    require(cases[f"{name}.SLDPRT"] == source_hashes[name]
            and cases["Build.json"] == report["build_sha256"]
            and report["packet_sha256"] == packet_sha
            and streams["cases"][name]["container"]["sha256"] == SOURCE_HASHES[name],
            "native result no longer binds its original model-generated candidates")
    if alternate:
        classic = json.loads((fixture / "Packet.json").read_bytes())
        comparison = (evidence_dir / "Compression.json").read_bytes()
        require(cases["Compression.json"] == digest(comparison)
                and streams["source_build_sha256"] == classic["files"]["Build.json"],
                "alternate packet is not linked to the classic stream witnesses")
    else:
        require(streams["source_build_sha256"] == report["build_sha256"],
                "classic packet is not linked to its logical stream witnesses")
    return json.loads(request), {"packet": packet, "result": result}, report, digest(request), streams["cases"][name]["streams"]


def plan_presentation(row):
    from convert.adapters.solidworks.Archive.Construction.Patterns.Drivers.PatDriveStyle import PatDriveStyle
    from convert.adapters.solidworks.Archive.Construction.Patterns.Input.PatAngleStyle import PatAngleStyle
    from convert.adapters.solidworks.Archive.Construction.Patterns.Input.PatPresentInput import PatPresentInput
    from convert.adapters.solidworks.Archive.Construction.Views.Annotations.AnnoViewInput import AnnoViewInput

    angle = row["angle"]
    return PatPresentInput(
        PatAngleStyle(
            angle["parameter_id"], angle["annotation_view"], angle["design_intent"],
            angle["selected_leader"], tuple(angle["shifted_point_m"]),
        ),
        row["count_parameter_id"], row["pitch_parameter_id"],
        tuple(PatDriveStyle(item["name"], item["annotation_view"], tuple(item["label_m"]),
                            item["design_intent"], item["selected_leader"])
              for item in row["styles"]),
        tuple(AnnoViewInput(item["name"], tuple(map(tuple, item["basis"]))) for item in row["views"]),
        row["active"], tuple(row["shown"]),
    )


def reject(call, reason, exception=ValueError):
    try:
        call()
    except exception as error:
        require(reason in str(error), f"unexpected refusal: {error}")
        return str(error)
    raise ValueError("unsupported pattern published successfully")


def check_rejections(document, readback, design, packet, native_path, values, public, direct, permissive):
    from convert.adapters.registry.RegistryErrors import NotFoundError
    from interchange.geometry.Models.Sketch import ConstraintRef, SketchRelation

    scope = document.feature_timeline
    pattern = scope[-1]
    _, pitch = pattern.parameter_ids
    driver = next(item for item in document.parameters if item.id == pitch)
    spacing = replace(driver.value, value=driver.value.value + 0.000125)
    changed = replace(
        document,
        feature_timeline=(*scope[:-1], replace(pattern, definition=replace(pattern.definition, spacing=spacing))),
        parameters=tuple(replace(item, value=spacing) if item is driver else item for item in document.parameters),
    )
    extra = replace(readback, metadata={**readback.metadata, "other_source_state": True})
    design_extra = replace(design, metadata={**design.metadata, "other_source_state": True})
    sketch = document.sketches[0]
    dimension = replace(driver, id="extra-sketch-width", name="Width", owner_id=sketch.id)
    relation = SketchRelation("extra-width-relation", "distance",
                              (ConstraintRef(sketch.entities[0].id),), dimension.id)
    dimensional = replace(
        document, parameters=(*document.parameters, dimension),
        sketches=(replace(sketch, parameter_ids=(dimension.id,), constraints=(*sketch.constraints, relation)),
                  *document.sketches[1:]),
    )
    dimensional.assert_valid()
    wrong_id = replace(values[PRESENTATION], PitchParamId="unowned pitch")
    failed_bind = {**values, PRESENTATION: wrong_id}
    evidence = values[MEASUREMENT]
    invalid_report = evidence | {"receipt": packet | {"result": b"{}"}}
    cases = (
        ("missing_receipt", document, {PRESENTATION: values[PRESENTATION], "final_destination": native_path},
         "requires an offline native measurement receipt"),
        ("receipt_changed", document, {**values, MEASUREMENT: invalid_report},
         "exact disclosed native measurement"),
        ("changed_pitch", changed, values, "no exact native linear pattern measurement"),
        ("changed_locator", document, {**values, "final_destination": rf"C:\Unmeasured\{PureWindowsPath(native_path).name}"},
         "no exact native linear pattern measurement"),
        ("changed_epoch", document, {**values, MEASUREMENT: evidence | {"written_at": evidence["written_at"] + 1}},
         "no exact native linear pattern measurement"),
        ("extra_source_domain", extra, {key: value for key, value in values.items() if key != PRESENTATION},
         "readback differs from its regenerated part"),
        ("extra_design_only_domain", design_extra, {key: value for key, value in values.items() if key != PRESENTATION},
         "readback differs from its regenerated part"),
        ("wrong_presentation_owner", document, failed_bind, "not bound to the actual active parameter owners"),
    )
    count = 0
    for _, model, options, reason in cases:
        for write in (public, direct):
            target = BytesIO(b"untouched output")
            target.seek(2)
            reject(lambda: write(model, target, options), reason)
            require((target.getvalue(), target.tell()) == (b"untouched output", 2), "refusal modified caller output")
            count += 1
    for write, error, reason in ((public, NotFoundError, "does not support the destination"),
                                 (direct, ValueError, "complete owned five operation document graph")):
        target = BytesIO(b"untouched output")
        target.seek(2)
        reject(lambda: write(dimensional, target, values), reason, error)
        require((target.getvalue(), target.tell()) == (b"untouched output", 2),
                "extra sketch driver modified caller output")
        count += 1
    target = BytesIO(b"untouched output")
    reject(lambda: permissive(changed, target, values), "no exact native linear pattern measurement")
    require(target.getvalue() == b"untouched output", "permissive policy bypassed native measurement")
    return count + 1


def check_compression_receipts(document, values, evidence, classic, public, direct):
    measurement = values[MEASUREMENT]
    wrongly_bound = "exact disclosed native measurement"
    rejected = 0
    for receipt, reason in (
        ({"packet": classic[0], "result": evidence["result"]}, wrongly_bound),
        ({"packet": evidence["packet"], "result": classic[1]}, wrongly_bound),
        (dict(zip(("packet", "result"), classic, strict=True)), "no exact native linear pattern measurement"),
    ):
        options = {**values, MEASUREMENT: {**measurement, "receipt": receipt}}
        for write in (public, direct):
            sink = BytesIO(b"untouched output")
            sink.seek(2)
            reject(lambda: write(document, sink, options), reason)
            require(sink.getvalue() == b"untouched output" and sink.tell() == 2,
                    "wrong-compression receipt modified caller output")
            rejected += 1
    return rejected


def check_semantics(readback, original, report):
    from interchange.Features.FeatureKinds import LinearPattern

    pattern, = (value for value in readback.feature_timeline if type(value.definition) is LinearPattern)
    model = pattern.definition
    body, = readback.bodies
    topology = body.topology
    cold = report["cold_geometry"]
    metric = cold["mass"]
    count, pitch = (next(value for value in readback.parameters if value.id == key)
                    for key in pattern.parameter_ids)
    authored = original.feature_timeline[-1].definition
    for authored_sketch, recovered_sketch in zip(original.sketches, readback.sketches, strict=True):
        for sketch in (authored_sketch, recovered_sketch):
            require(not sketch.parameter_ids
                    and all(item.parameter_id is None and item.driving and not item.suppressed
                            for item in sketch.constraints)
                    and sorted(item.kind for item in sketch.constraints) == [
                        "horizontal", "horizontal", "vertical", "vertical"],
                    "the supported rectangle scope requires four live relations with no sketch dimensions")
    require(readback.brep is not None and not readback.brep_payloads
            and body.final_feature_id == pattern.id
            and len(readback.configurations) == 1 and readback.configurations[0].active
            and readback.configurations[0].name == original.configurations[0].name
            and tuple(len(sketch.constraints) for sketch in readback.sketches) == (4, 4)
            and len(readback.selections) == 7
            and count.name == "D1" and count.value.value == model.instance_count == authored.instance_count
            and pitch.name == "D3" and pitch.value == model.spacing and pitch.value.unit == "mm"
            and isclose(pitch.value.value, authored.spacing.value * 1000.0)
            and model.reversed == authored.reversed,
            "strict readback changed a scoped native creation owner or driver")
    require(topology.solid_count == cold["body_count"] == 1
            and topology.face_count == cold["face_count"]
            and isclose(topology.volume, metric["volume"] * 1e9, rel_tol=5e-7)
            and isclose(topology.surface_area, metric["area"] * 1e6, rel_tol=5e-7)
            and all(isclose(value, target * 1000.0, rel_tol=5e-7)
                    for value, target in zip(body.attributes["solidworks.body_centroid_mm"], metric["com"], strict=True)),
            "strict SDK geometry differs from the independently measured native solid")
    readback.assert_valid()
    return {"faces": topology.face_count, "edges": topology.edge_count, "vertices": topology.vertex_count,
            "volume_mm3": topology.volume, "area_mm2": topology.surface_area, "count": model.instance_count,
            "pitch_mm": pitch.value.value, "reversed": model.reversed}


def check_design_history(payload, full, open_document, open_archive, build_archive):
    from convert.adapters.solidworks.Core.Adapter import KSourceSemanticShaTwoFive, SemanticShaTwo
    from interchange.Enums.EnumDocument import Capability

    design = open_document(BytesIO(payload), source_format=FORMAT, strict=True, include_brep=False)
    expected = replace(full, brep=None, capabilities=full.capabilities - {Capability.BREP})
    expect_digest = SemanticShaTwo(expected)
    require(full.metadata[KSourceSemanticShaTwoFive] == SemanticShaTwo(full),
            "full read no longer owns its derived geometry in the semantic digest")
    expected = replace(expected, metadata={**expected.metadata, KSourceSemanticShaTwoFive: expect_digest})
    require(design == expected, "design-only pattern lost a typed owner or source domain")
    streams = dict(open_archive(payload).streams)
    del streams["Contents/CMgr"]
    unqualified = build_archive(streams, FormatVersion=4)
    for geometry in (True, False):
        reject(lambda: open_document(BytesIO(unqualified), source_format=FORMAT, strict=True,
                                     include_brep=geometry),
               "cache-free linear pattern lacks a verified typed feature history")
    return design, unqualified


def check_permissive_history(unqualified, design, open_document):
    from interchange.Features.FeatureKinds import LinearPattern

    permissive = open_document(BytesIO(unqualified), source_format=FORMAT, strict=False, include_brep=False)
    pattern, = (item for item in design.feature_timeline if type(item.definition) is LinearPattern)
    incomplete, = (item for item in permissive.feature_timeline if item.name == pattern.name)
    require(type(incomplete.definition) is not LinearPattern and permissive.brep is None,
            "permissive incomplete archive gained unverified typed history")


def capture_candidate(directory, raw, report, root):
    directory.mkdir(exist_ok=False)
    with (directory / f"{report['case']}.SLDPRT").open("xb") as output:
        output.write(raw)
    bindings = {
        **report,
        "capture_schema": "kit.sw2026.pattern-compression-capture.v1",
        "worker_sha256": digest(HERE.read_bytes()),
        "sdk_source_sha256": tree_digest(root / "src"),
        "python_version": sys.version,
        "runtime_platform": sys.platform,
        "worker_pid": getpid(),
    }
    with (directory / "Capture.json").open("xb") as output:
        output.write((json.dumps(bindings, sort_keys=True, indent=2, allow_nan=False) + "\n").encode())
    return bindings


def tree_digest(directory):
    source = sha256()
    entries = (path.relative_to(directory) for path in directory.rglob("*") if path.is_file())
    for relative in sorted(entries, key=lambda path: path.as_posix()):
        if "__pycache__" not in relative.parts and relative.suffix != ".pyc":
            path = directory / relative
            source.update(relative.as_posix().encode())
            source.update(b"\0")
            source.update(sha256(path.read_bytes()).digest())
    return source.hexdigest()


def verify(root, name, scratch, verify_runtime_boundary, capture=None, alternate=False):
    scratch = scratch.resolve()
    request, evidence, result, request_sha, expected_streams = read_inputs(root, name, alternate)
    expected_hash = (ALTERNATE_HASHES if alternate else SOURCE_HASHES)[name]
    classic = read_bound_receipt(root / FIXTURES, PACKET_SHA, RESULT_SHA) if alternate else None
    sys.path.insert(0, str(root / "src"))
    from convert import extract_brep, open_document, write_document
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.base.WritePolicy import GetDocumentCaps
    from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
    from convert.adapters.solidworks.Core.Preparation.Patterns.PreparePat import PreparePat
    from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
    from interchange import CadDocument

    for module in (
        "interchange.brep.Validation.BrepValidate",
        "interchange.document.Behavior.DocumentIo",
        "interchange.document.Models.DocumentProvenance",
        "interchange.document.Validation.DocumentAssemblyValidate",
        "interchange.document.Validation.DocumentFeatureValidate",
        "interchange.document.Validation.DocumentReferenceValidate",
    ):
        import_module(module)
    for codec in ("utf-8", "utf-16-le", "latin-1", "cp1252"):
        lookup(codec)
    presentation = plan_presentation(request["presentation"])
    parsed = CadDocument.from_json(json.dumps(request["document"]))
    native_path = request["target"]["PathName"]
    values = {
        "final_destination": native_path,
        "require_native_transfers": True,
        PRESENTATION: presentation,
        MEASUREMENT: {"written_at": request["target"]["SavedAt"], "receipt": evidence},
    }
    reopen_values = {key: value for key, value in values.items() if key != PRESENTATION}
    writer = SldprtWriter()

    def public(doc, target, options):
        return write_document(doc, target, destination_format=FORMAT, values=options, allow_carrier=False)

    def direct(doc, target, options):
        return writer.write(doc, target, WriteOptions(values=options))

    def permissive(doc, target, options):
        return write_document(doc, target, destination_format=FORMAT, values=options, allow_carrier=True)

    blocked = []
    active = False

    def audit(event, args):
        if active and event == "open" and isinstance(args[0], str):
            path = Path(args[0])
            if path.is_relative_to(scratch) and path.is_dir():
                return
        if active and event in ("open", "subprocess.Popen", "os.system", "os.exec", "os.posix_spawn", "ctypes.dlopen"):
            blocked.append(event)
            raise RuntimeError(f"pattern worker attempted filesystem or CAD launch: {event}")

    @contextmanager
    def guard():
        nonlocal active
        active = True
        try:
            yield
        finally:
            active = False

    sys.addaudithook(audit)
    if not alternate and verify_runtime_boundary and "zlib-ng" in ZLIB_RUNTIME_VERSION:
        with guard():
            prepared = PreparePat(parsed, BytesIO(), request["target"]["SavedAt"],
                                  WriteOptions(values={"final_destination": native_path}), presentation)
            if digest(prepared) != SOURCE_HASHES[name]:
                readback = open_document(BytesIO(prepared), source_format=FORMAT, strict=True)
                semantic = check_semantics(readback, parsed, result["phases"][f"{name}-edit"])
                design, incomplete = check_design_history(prepared, readback, open_document,
                                                          SldprtArchive.from_bytes, BuildSldprt)
                for write in (public, direct):
                    untouched = BytesIO()
                    reject(lambda: write(parsed, untouched, values), "no exact native linear pattern measurement")
                    require(untouched.getvalue() == b"", "unmeasured compressor published an archive")
                streams = stream_manifest(SldprtArchive.from_bytes(prepared))
                require(streams == expected_streams and not blocked, "alternate runtime changed logical streams")
        if digest(prepared) != SOURCE_HASHES[name]:
            check_permissive_history(incomplete, design, open_document)
            report = {"case": name, "request_sha256": request_sha, "generated_sha256": digest(prepared),
                      "bytes": len(prepared), "streams": streams, "publication_count": 0, "refusal_count": 2,
                      "runtime_input_file_reads": len(blocked), "native_launches": 0, "semantics": semantic,
                      "design_only_history_equal": True, "strict_history_refusal_count": 2,
                      "permissive_history_unqualified": True,
                      "compression_runtime": ZLIB_RUNTIME_VERSION, "status": "unmeasured_binary_envelope_refused"}
            return capture_candidate(capture, prepared, report, root) if capture else report
    original, direct_output, retained, direct_retained = (BytesIO() for _ in range(4))
    target = scratch / (name + ".SLDPRT")
    with target.open("xb") as file_sink, guard():
        neutral_results = [public(parsed, original, values), direct(parsed, direct_output, values),
                           public(parsed, file_sink, values)]
        raw = original.getvalue()
        readback = open_document(BytesIO(raw), source_format=FORMAT, strict=True)
        design, incomplete = check_design_history(raw, readback, open_document, SldprtArchive.from_bytes, BuildSldprt)
        snapshot = CadDocument.from_json(readback.to_json())
        design_snapshot = CadDocument.from_json(design.to_json())
        design_sinks = (BytesIO(), BytesIO())
        readback_results = [public(readback, retained, reopen_values), direct(snapshot, direct_retained, reopen_values)]
        design_results = [public(design_snapshot, design_sinks[0], reopen_values),
                          direct(design, design_sinks[1], reopen_values)]
        require(digest(raw) == expected_hash
                and direct_output.getvalue() == retained.getvalue() == direct_retained.getvalue() == raw
                and all(sink.getvalue() == raw for sink in design_sinks),
                "measured registry or direct model and readback publication diverged")
        for doc, results in ((parsed, neutral_results), (readback, readback_results), (design, design_results)):
            require(all(item.vendor_loadable and item.application_usable and not item.dropped
                        and item.bytes_written == len(raw) and item.native_capabilities == GetDocumentCaps(doc)
                        and item.metadata[MEASUREMENT]["generated_sha256"] == digest(raw)
                        and item.metadata[MEASUREMENT]["packet_sha256"] == digest(evidence["packet"])
                        and item.metadata[MEASUREMENT]["native_result_sha256"] == digest(evidence["result"])
                        for item in results),
                    "every published pattern must retain complete native transfer evidence")
        semantics = check_semantics(readback, parsed, result["phases"][f"{name}-edit"])
        refused = check_rejections(parsed, readback, design, evidence, native_path, values, public, direct, permissive)
        compression_refused = 0 if classic is None else check_compression_receipts(
            parsed, values, evidence, classic, public, direct,
        )
    check_permissive_history(incomplete, design, open_document)
    path_source = open_document(target, source_format=FORMAT, strict=True)
    require(path_source.feature_timeline == readback.feature_timeline and path_source.bodies == readback.bodies,
            "strict path and binary input describe different pattern owners")
    require(target.read_bytes() == raw and not blocked, "owned file sink differs or worker accessed disk")
    unmeasured = scratch / "Other" / target.name
    unmeasured.parent.mkdir()
    unmeasured.write_bytes(b"prior path")
    with guard():
        reject(lambda: write_document(parsed, unmeasured, overwrite=True, values=values, allow_carrier=False),
               "no exact native linear pattern measurement")
    require(unmeasured.read_bytes() == b"prior path" and tuple(unmeasured.parent.iterdir()) == (unmeasured,),
            "failed measured path replacement changed the prior file or left staging artifacts")
    raw_path = scratch / "Raw"
    reject(lambda: extract_brep(raw, raw_path, source_format=FORMAT), "no readable Parasolid payload")
    require(not raw_path.exists() and not any(module.startswith(("win32com", "pythoncom")) for module in sys.modules),
            "absent raw extraction produced output or imported a CAD runtime")
    streams = stream_manifest(SldprtArchive.from_bytes(raw))
    require(streams == expected_streams, "complete file did not retain all independently pinned logical streams")
    report = {"case": name, "request_sha256": request_sha,
            "generated_sha256": digest(raw), "bytes": len(raw),
            "streams": streams, "publication_count": len(neutral_results) + len(readback_results) + len(design_results),
            "refusal_count": refused + 2, "runtime_input_file_reads": len(blocked), "native_launches": 0,
            "design_only_history_equal": True, "strict_history_refusal_count": 2,
            "permissive_history_unqualified": True,
            "semantics": semantics, "compression_runtime": ZLIB_RUNTIME_VERSION, "status": "native_hash_reproduced"}
    if alternate:
        report["compression_receipt_refusal_count"] = compression_refused
    return capture_candidate(capture, raw, report, root) if capture else report


def stream_manifest(archive):
    return {record.name: [len(record.data), digest(record.data)] for record in archive.records}


def main():
    parser = ArgumentParser(description="Verify one exact disclosed measured pattern from neutral data in a fresh process")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--case", choices=tuple(SOURCE_HASHES), required=True)
    parser.add_argument("--verify-runtime-boundary", action="store_true")
    parser.add_argument("--capture-candidate", type=Path)
    parser.add_argument("--alternate-receipt", action="store_true")
    args = parser.parse_args()
    with TemporaryDirectory(prefix="KitMeasuredPattern-") as directory:
        report = verify(args.root.resolve(), args.case, Path(directory),
                        args.verify_runtime_boundary or args.capture_candidate is not None,
                        args.capture_candidate, args.alternate_receipt)
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
