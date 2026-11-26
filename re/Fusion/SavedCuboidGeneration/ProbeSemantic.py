import argparse
import base64
from collections import Counter
from hashlib import sha256
from io import BytesIO
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time


CONFIG_ENV = "KIT_SEMANTIC_PROBE_CONFIG"
AUDIT_ACTIVE = False
AUDIT_WRITING = False


def digest(payload):
    return sha256(payload).hexdigest()


def install_audit():
    global AUDIT_ACTIVE
    if AUDIT_ACTIVE:
        return
    config = json.loads(Path(os.environ[CONFIG_ENV]).read_text(encoding="utf-8"))
    root = Path(config["root"]).resolve()
    request = Path(config["request"]).resolve()
    destination = Path(config["destination"]).resolve()
    audit_path = Path(config["audit"]) / f"Process{os.getpid()}.jsonl"
    child = [sys.executable, "-B", str(root / "re/automation/EncoderRoundTrip/Fusion.py"), "--kit-fusion-encoder-child"]

    def record(value):
        global AUDIT_WRITING
        AUDIT_WRITING = True
        try:
            with audit_path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(value) + "\n")
        finally:
            AUDIT_WRITING = False

    def audit(event, arguments):
        if AUDIT_WRITING:
            return
        denied = None
        if event == "open" and isinstance(arguments[0], (str, bytes, os.PathLike)):
            path = Path(os.fsdecode(arguments[0])).resolve()
            protected = any(path.is_relative_to(root / name) for name in ("re", "tests", "examples"))
            native = path.suffix.lower() in (".f3d", ".f3z", ".sldprt", ".sldasm", ".fcstd")
            permitted = path in (request, destination)
            if not permitted and (native or (protected and path.suffix.lower() not in (".py", ".pyc", ".pyd", ".so"))):
                denied = f"archive or research data read refused: {path}"
        elif event == "subprocess.Popen":
            actual = arguments[1]
            matches = actual == child or actual == subprocess.list2cmdline(child)
            environment = arguments[3]
            inherited = environment is None or environment.get(CONFIG_ENV) == os.environ[CONFIG_ENV]
            if not matches or not inherited:
                denied = "unapproved subprocess launch"
            record({"event": event, "allowed": denied is None, "argv": actual})
        elif event in ("os.system", "os.startfile", "os.exec", "os.posix_spawn", "socket.connect", "socket.getaddrinfo"):
            denied = f"runtime or network operation refused: {event}"
        elif event == "import" and str(arguments[0]).split(".")[0] in ("adsk", "win32com", "comtypes", "pythoncom", "clr"):
            denied = f"vendor automation import refused: {arguments[0]}"
        if denied:
            record({"event": event, "denied": denied})
            raise PermissionError(denied)

    AUDIT_ACTIVE = True
    sys.addaudithook(audit)
    record({"event": "audit_started", "pid": os.getpid(), "argv": sys.argv,
            "probe_sha256": digest(Path(__file__).read_bytes())})


def near(actual, expected):
    if not math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12):
        raise AssertionError(f"semantic quantity changed: {actual!r} != {expected!r}")


def verify_candidate(path, request, receipt):
    from convert import open_document, write_document
    from convert.adapters.Fusion.Bridge.CheckContract import CheckContract
    from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
    from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
    from interchange import CadDocument

    payload = path.read_bytes()
    document = open_document(payload, source_format="f3d")
    model = ReadDocument(payload)
    assert not document.diagnostics and not document.brep_payloads
    assert set(document.metadata) == {"fusion.native_state"}
    assert CheckContract(document.metadata["fusion.native_state"], "model", 1) == model
    neutral_path = path.with_suffix(".json")
    neutral_path.write_text(document.to_json(), encoding="utf-8", newline="\n")
    restored = CadDocument.from_json(neutral_path.read_text(encoding="utf-8"))
    assert restored == document
    stream = BytesIO()
    write_document(restored, stream, destination_format="f3d", allow_carrier=False)
    assert stream.getvalue() == payload
    assert len(document.bodies) == 1 and len(document.sketches) == 1
    assert len(document.feature_timeline) == 2 and len(document.parameters) == 7
    assert document.configurations[0].name == request["title"]
    assert document.sketches[0].name == request["names"]["sketch"]
    assert document.feature_timeline[-1].name == request["names"]["extrude"]
    assert document.bodies[0].name == request["names"]["body"]
    parameters = {value.name: value for value in document.parameters}
    for role, name in request["drivers"].items():
        near(parameters[name].value.value, request["dimensions_mm"][role])
    by_id = {value.id: value for value in document.parameters}
    drivers = set()
    for relation in document.sketches[0].constraints:
        if relation.parameter_id:
            parameter = by_id[relation.parameter_id]
            assert parameter.expression is not None
            assert len(parameter.expression.parameter_ids) == 1
            drivers.update(parameter.expression.parameter_ids)
    assert drivers == {parameters[request["drivers"][role]].id for role in ("width", "depth")}
    definition = document.feature_timeline[-1].definition
    assert definition.SideMode == "one_sided"
    along = by_id[definition.AlongParameterId]
    assert along.expression.parameter_ids == (parameters[request["drivers"]["height"]].id,)
    sizes = request["dimensions_mm"]
    near(document.bodies[0].topology.volume, sizes["width"] * sizes["depth"] * sizes["height"])
    bounds = document.bodies[0].topology.bounding_box
    for value in (bounds.minimum.x, bounds.minimum.y, bounds.minimum.z):
        near(value, 0)
    for value, role in zip((bounds.maximum.x, bounds.maximum.y, bounds.maximum.z), ("width", "depth", "height"), strict=True):
        near(value, sizes[role])
    material = document.materials[0]
    assert material.EntityName == request["material"]["label"]
    near(material.Density, request["material"]["density_kg_m3"])
    for value, expected in zip(material.ColorValue, request["material"]["rgba"], strict=True):
        near(value, expected)
    assert Counter(value.kind for value in document.sketches[0].constraints) == {
        "horizontal": 2, "vertical": 2, "distance_x": 1, "distance_y": 1}
    graph = BuildGraph(model)
    points = graph.ByClass("Point3D")
    assert len(points) == 5 and len(graph.ByClass("SketchGeomConstraint")) == 4
    fixed = [value for value in points if value.Fields["isFixed"]]
    assert len(fixed) == 2 and sum(value.Fields["isOrigin"] for value in fixed) == 1
    assert not model.Snapshots and not model.Configurations and model.Graphics is None
    assert receipt["candidate_sha256"] == digest(payload)
    assert receipt["source_free_constructor"] is True
    assert receipt["whole_saved_source_admission"] is False
    assert receipt["vendor_loadable"] is False and receipt["application_usable"] is False
    for key, expected in request.items():
        if key != "schema":
            assert receipt["semantics"][key] == expected
    return {"candidate_sha256": digest(payload), "native_contract_equal": True,
            "persisted_document_sha256": digest(neutral_path.read_bytes()),
            "public_reemission_identical": True, "dimensions_mm": sizes,
            "volume_mm3": document.bodies[0].topology.volume,
            "native_point_count": len(points), "native_fixed_point_count": len(fixed)}


def run_case(root, output, producer, name, request, epoch, accepts, occupied=False):
    started = time.monotonic()
    folder = output / name
    folder.mkdir()
    request_path = folder / "Request.json"
    request_path.write_text(json.dumps(request, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    destination = folder / "Candidate.f3d"
    if occupied:
        destination.write_bytes(b"preserve occupied destination")
    audit_folder = folder / "Audit"
    audit_folder.mkdir()
    config = folder / "AuditConfig.json"
    config.write_text(json.dumps({"root": str(root), "request": str(request_path),
                                 "destination": str(destination), "audit": str(audit_folder)}), encoding="utf-8")
    environment = dict(os.environ)
    environment[CONFIG_ENV] = str(config)
    environment["PYTHONPATH"] = os.pathsep.join((str(output / "AuditSupport"), str(Path(__file__).parent), str(root / "src"), str(root / "Cli")))
    result = subprocess.run([sys.executable, "-B", str(producer), str(request_path), str(destination), "--written-at", str(epoch)],
                            cwd=folder, env=environment, capture_output=True, text=True, timeout=120, check=False)
    (folder / "Stdout.txt").write_text(result.stdout, encoding="utf-8")
    (folder / "Stderr.txt").write_text(result.stderr, encoding="utf-8")
    events = [json.loads(line) for path in sorted(audit_folder.glob("Process*.jsonl")) for line in path.read_text(encoding="utf-8").splitlines()]
    starts = [event for event in events if event["event"] == "audit_started"]
    launches = [event for event in events if event["event"] == "subprocess.Popen"]
    row = {"name": name, "request_sha256": digest(request_path.read_bytes()),
           "returncode": result.returncode, "processes": starts, "child_launches": launches,
           "expected_acceptance": accepts}
    try:
        assert len(starts) == len(launches) + 1
        assert not any("denied" in event for event in events)
        assert "Error in sitecustomize" not in result.stderr
        if accepts:
            assert result.returncode == 0, result.stdout + result.stderr
            receipt = json.loads(result.stdout)
            row["producer_receipt"] = receipt
            row.update(verify_candidate(destination, request, receipt))
            assert len(starts) >= 2
        else:
            assert result.returncode != 0, "unsupported request was accepted"
            if occupied:
                assert destination.read_bytes() == b"preserve occupied destination"
            else:
                assert not destination.exists(), "refused input published a native candidate"
            assert any(word in (result.stdout + result.stderr).lower() for word in
                       ("unknown", "unexpected", "missing", "required", "unsupported", "schema", "source", "exists", "present", "overwrite"))
        row["passed"] = True
    except (AssertionError, KeyError, TypeError, ValueError, AttributeError) as error:
        row.update(passed=False, error_type=type(error).__name__, error=str(error))
    row["elapsed_seconds"] = round(time.monotonic() - started, 3)
    (folder / "CaseResult.json").write_text(json.dumps(row, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"case": name, "passed": row["passed"], "seconds": row["elapsed_seconds"],
                      "error": row.get("error")}), flush=True)
    return row


def main():
    started = time.monotonic()
    parser = argparse.ArgumentParser(description="Probe fresh archive-free semantic constructor generation; no native acceptance claims")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--producer", type=Path, default=Path(__file__).with_name("GenerateSemantic.py"))
    parser.add_argument("--original", type=Path)
    parser.add_argument("--written-at", type=int, default=1795564800)
    parser.add_argument("--producer-sha256", default="9376e46d309ba2729d82d4c930dd73e1e1843fcae51280aa5d1ae8f054941131")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    producer = args.producer.resolve()
    producer_digest = digest(producer.read_bytes())
    if producer_digest != args.producer_sha256:
        raise ValueError("Producer differs from the frozen revision")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    support = output / "AuditSupport"
    support.mkdir()
    (support / "sitecustomize.py").write_text("from ProbeSemantic import install_audit\ninstall_audit()\n", encoding="utf-8")
    source = args.original or root / "re/Fusion/SavedCuboidRoundTrip/Corpus/BaselineControl.f3d"
    original = source.read_bytes()
    unavailable = output / "TestOwnedOriginal.f3d"
    unavailable.write_bytes(original)
    original_digest = digest(unavailable.read_bytes())
    unavailable.unlink()
    base = {"schema": 1, "title": "Semantic Cuboid Probe",
            "dimensions_mm": {"width": 16.4, "depth": 27.1, "height": 13.8},
            "drivers": {"width": "probeWidth", "depth": "probeDepth", "height": "probeHeight"},
            "names": {"sketch": "Probe Profile", "extrude": "Probe Extrusion", "body": "Probe Solid"},
            "material": {"label": "Probe Physical", "density_kg_m3": 1100, "rgba": [0.25, 0.5, 0.75, 1]}}
    clone = lambda value: json.loads(json.dumps(value))
    height = clone(base)
    height["dimensions_mm"]["height"] = 22.6
    depth = clone(base)
    depth["dimensions_mm"]["depth"] = 19.7
    procedural = clone(base)
    procedural["material"]["procedural_mapping"] = {"kind": "wood", "origin": [1, 2, 3]}
    archive = clone(base)
    archive["source_archive_b64"] = base64.b64encode(original[:128]).decode("ascii")
    missing = clone(base)
    del missing["drivers"]
    source_path = clone(base)
    source_path["source_path"] = str(unavailable)
    cases = (("BaselineOne", base, True, False), ("BaselineTwo", base, True, False),
             ("ExtrusionDepthEdit", height, True, False), ("ProfileDepthEdit", depth, True, False),
             ("ProceduralRefusal", procedural, False, False), ("ArchiveBytesRefusal", archive, False, False),
             ("MissingStateRefusal", missing, False, False), ("SourcePathRefusal", source_path, False, False),
             ("OccupiedDestination", base, False, True))
    rows = []
    for name, request, accepts, occupied in cases:
        assert not unavailable.exists()
        assert digest(producer.read_bytes()) == producer_digest
        rows.append(run_case(root, output, producer, name, request, args.written_at, accepts, occupied))
    identical = rows[0].get("candidate_sha256") == rows[1].get("candidate_sha256") and "candidate_sha256" in rows[0]
    report = {"scope": "source-free constrained constructor only; whole saved-source admission and native acceptance unqualified",
              "whole_saved_source_admission": False, "native_acceptance_measured": False,
              "producer_sha256": producer_digest, "probe_sha256": digest(Path(__file__).read_bytes()),
              "elapsed_seconds": round(time.monotonic() - started, 3),
              "archive_refusal_input_scope": "128 original archive bytes embedded as an unsupported request field below the request size limit",
              "written_at": args.written_at, "test_owned_original_sha256": original_digest,
              "test_owned_original_unavailable": not unavailable.exists(),
              "deterministic_two_process_runs": identical, "cases": rows}
    (output / "Report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"report": str(output / "Report.json"), "passed": sum(row["passed"] for row in rows),
                      "total": len(rows), "deterministic": identical}))
    return 0 if identical and all(row["passed"] for row in rows) else 3


if __name__ == "__main__":
    raise SystemExit(main())
