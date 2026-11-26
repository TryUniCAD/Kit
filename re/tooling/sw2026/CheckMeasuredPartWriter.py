from argparse import ArgumentParser
from codecs import lookup
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from io import BytesIO
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE.parent))
from CheckScopedPlainWriter import WriterAudit, readback, read_cold_geometry, reject

FORMAT = "solidworks.sldprt"
OPTION = "solidworks_native_measurement"


def demand(condition, message):
    if not condition:
        raise ValueError(message)


def digest(raw):
    return sha256(raw).hexdigest()


def read_pinned(path, expected):
    raw = path.read_bytes()
    demand(digest(raw) == expected, f"disclosed evidence changed: {path.name}")
    return json.loads(raw)


def check_custody(directory, receipt):
    terminal = read_pinned(directory / "Inspection/Result.json", receipt["native_result_sha256"])
    packet = read_pinned(directory / "Packet.json", receipt["packet_sha256"])
    proof = read_pinned(directory / "BuildProof.json", receipt["generation_report_sha256"])
    demand(terminal["passed"] and terminal["controls_healthy"] and terminal["inputs_unchanged"]
           and terminal["cases"] == receipt["cases"] and terminal["packet_sha256"] == receipt["packet_sha256"]
           and terminal["distinct_processes"] == receipt["distinct_native_processes"]
           and proof["passed"] and proof["runtime_reads"] == 0
           and packet["oracle_sha256"] == receipt["oracle"]["sha256"]
           and packet["build_proof_sha256"] == receipt["generation_report_sha256"],
           "archived oracle report did not bind the measured packet")
    observations = terminal["phases"]
    demand(list(observations) == [phase["role"] for phase in receipt["phases"]]
           and len({(row["oracle_identity"]["process_id"], row["oracle_identity"]["process_creation_filetime"])
                    for row in observations.values()}) == len(observations),
           "terminal does not establish distinct native lifetimes")
    for phase in receipt["phases"]:
        label = phase["role"]
        row = observations[label]
        _ = read_pinned(directory / "Inspection" / label / "Record.json", phase["record_sha256"])
        identity = row["oracle_identity"]
        demand(row["passed"] and identity["version_matches"]
               and identity["sha256"] == packet["oracle_sha256"]
               and row["record_sha256"] == phase["record_sha256"],
               "native lifetime or receipt differs")
        if not label.startswith("Control"):
            demand((row["open_errors"], row["open_warnings"]) == (0, 0)
                   and not row["dialogs"] and not row["controller_diagnostics"]
                   and row["immutable_bytes"] and row["numeric_check_count"] == phase["numeric_checks"],
                   "candidate did not cleanly load and measure")
    return proof["written_at"]


def run_refusals(doc, target, request, audit, writer, write_document, WriteOptions):
    value = request["evidence"]
    cases = {"missing_receipt": (doc, None, "requires an offline native measurement receipt"),
             "different_epoch": (doc, value | {"written_at": value["written_at"] + 1}, "no unique exact native measurement")}
    for label, change, message in (
        ("bad_build", lambda receipt: receipt["oracle"].update(build="34.0.0.0"), "exact passing SOLIDWORKS"),
        ("failed_control", lambda receipt: receipt["phases"][0].update(passed=False), "failed an oracle phase"),
        ("missing_digests", lambda receipt: receipt.update(native_result_sha256=""), "canonical SHA-256"),
        ("missing_reopen", lambda receipt: next(row for row in receipt["phases"] if row["role"] == request["role"] + "Reopen").update(role="UnownedReopen"), "matched candidate lifecycle"),
        ("unclean_generated", lambda receipt: next(row for row in receipt["phases"] if row["role"] == request["role"] + "Generated")["states"][0].update(warnings=1), "unclean solid observation"),
    ):
        tampered = deepcopy(value)
        change(tampered["receipt"])
        cases[label] = doc, tampered, message
    boss, = doc.feature_timeline
    depth, = doc.parameters
    new_depth = replace(depth.value, value=depth.value.value + 1)
    changed = replace(doc, parameters=(replace(depth, value=new_depth),),
                      feature_timeline=(replace(boss, definition=replace(boss.definition, length=new_depth)),))
    cases["changed_model"] = changed, value, "no unique exact native measurement"
    initial = audit.target_opens
    buffer = BytesIO(b"preserve stream")
    buffer.seek(3)
    for model, evidence, message in cases.values():
        options = {"final_destination": request["expected_locator"]}
        if evidence is not None:
            options[OPTION] = evidence
        reject(lambda: write_document(model, target, overwrite=True, validate=False, allow_carrier=True,
                                      values=options), ValueError, message)
        reject(lambda: writer.write(model, buffer, WriteOptions(values=options, validate=False)),
               ValueError, message)
    wrong_locator = {OPTION: value, "final_destination": "C:\\UnmeasuredOutput\\" + target.name}
    reject(lambda: writer.write(doc, buffer, WriteOptions(values=wrong_locator)),
           ValueError, "no unique exact native measurement")
    demand(audit.target_opens == initial and buffer.tell() == 3 and buffer.getvalue() == b"preserve stream",
           "a refused publication opened or changed an output")
    return sorted([*cases, "different_locator"])



def check_retained_policy(doc, target, stream, evidence, write_document):
    from convert.adapters.registry.RegistryErrors import NotFoundError

    options = {"destination_format": FORMAT, "values": evidence}
    unknown = replace(doc, metadata={**doc.metadata, "unmodeled": True})
    sketch, = doc.sketches
    edge = sketch.entities[-1]
    end = replace(edge.geometry.end, x=edge.geometry.end.x + .5)
    loop = replace(sketch, entities=(*sketch.entities[:-1], replace(edge, geometry=replace(edge.geometry, end=end))))
    broken = replace(doc, sketches=(loop,))
    negative = (
        ("unnamed_stream", lambda: write_document(doc, stream, destination_format=FORMAT,
                                                 values={OPTION: evidence[OPTION]}), ValueError, "unnamed native streams"),
        ("unknown_model_data", lambda: write_document(unknown, stream, **options), NotFoundError, "does not support the destination"),
        ("disconnected_loop", lambda: write_document(broken, stream, **options), NotFoundError, "does not support the destination"),
        ("unmodeled_configuration", lambda: write_document(doc, stream, configuration="missing", **options),
         ValueError, "requested write configuration is unavailable"),
        ("unsupported_extension", lambda: write_document(doc, target.with_suffix(".SLDASM"), values=evidence),
         NotFoundError, "no writer supports the destination"),
        ("overwrite_guard", lambda: write_document(doc, target, values=evidence), FileExistsError, target.name),
    )
    for name, operation, error, reasoning in negative:
        reject(operation, error, reasoning)
    return [item[0] for item in negative]


def worker(root, request, directory):
    sys.path.insert(0, str(root / "src"))
    target = directory / (request["document"]["metadata"]["name"] + ".SLDPRT")
    audit = WriterAudit(root / "src", target)
    sys.addaudithook(audit.observe)
    from convert import write_document
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.solidworks.Core.Preparation.PrepareNative import PrepareNative
    from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
    from interchange.document.Models.DocumentModel import CadDocument
    for module in ("interchange.document.Behavior.DocumentIo", "interchange.document.Models.DocumentProvenance",
                   "interchange.document.Validation.DocumentAssemblyValidate",
                   "interchange.document.Validation.DocumentFeatureValidate",
                   "interchange.document.Validation.DocumentReferenceValidate"):
        import_module(module)
    for codec in ("utf-8", "utf-16-le", "latin-1", "cp1252"):
        lookup(codec)
    doc = CadDocument.from_json(json.dumps(request["document"]))
    writer = SldprtWriter()
    expected = request["sha256"]
    archive_path = request["expected_locator"]
    write_values = {"final_destination": archive_path, "require_native_transfers": True, OPTION: request["evidence"]}
    audit.phase = "done"
    target.write_bytes(b"preserve existing path")
    audit.phase = "write"
    refusals = run_refusals(doc, target, request, audit, writer, write_document, WriteOptions)
    audit.phase = "done"
    demand(target.read_bytes() == b"preserve existing path" and tuple(directory.iterdir()) == (target,),
           "a refused publication changed the path or left staging data")
    audit.phase = "write"
    internal = PrepareNative(doc, BytesIO(), request["evidence"]["written_at"],
                             WriteOptions(values={"final_destination": archive_path}))
    stream, direct = BytesIO(), BytesIO()
    prior_operations = check_retained_policy(doc, target, stream, write_values, write_document)
    demand(not stream.getvalue(), "a prior ordinary policy refusal wrote bytes")
    outcomes = [
        write_document(doc, stream, destination_format=FORMAT, allow_carrier=False, values=write_values),
        writer.write(doc, direct, WriteOptions(values=write_values)),
    ]
    host_file = os.name != "nt"
    if host_file:
        outcomes.append(write_document(doc, target, overwrite=True, allow_carrier=False, values=write_values))
    audit.phase = "done"
    raw = stream.getvalue()
    demand(digest(raw) == expected and direct.getvalue() == internal.BytesValue == raw
           and (not host_file or target.read_bytes() == raw)
           and all(outcome.bytes_written == len(raw) and outcome.vendor_loadable and outcome.application_usable
                   and not outcome.dropped and outcome.metadata[OPTION]["generated_sha256"] == expected
                   for outcome in outcomes)
           and len(outcomes[0].native_capabilities) == 6
           and tuple(directory.iterdir()) == (target,)
           and not audit.denied and audit.target_opens == int(host_file),
           "public output diverges from the exact native measurement or crossed the runtime guard")
    demand(not any(name.startswith(("pythoncom", "win32com")) for name in sys.modules),
           "writer imported a CAD runtime")
    from convert import extract_brep
    from convert.adapters.solidworks.Container.Container import SldprtFormatError

    reject(lambda: extract_brep(raw, directory / "raw", source_format=FORMAT),
           SldprtFormatError, "SLDPRT contains no readable Parasolid payload")
    demand(not (directory / "raw").exists(), "absent cache extraction created a destination")
    geometry = read_cold_geometry(raw, doc)
    state = readback(raw, raw, doc, archive_path)
    return {"role": request["role"], "sha256": expected, "bytes": len(raw),
            "measurements_accepted": len(outcomes), "target_file_opens": audit.target_opens,
            "native_capabilities": sorted(value.value for value in outcomes[0].native_capabilities),
            "default_geometry": geometry, "readback": state,
            "resolved_stream_bytes": len(internal.StreamsValue["Contents/Config-0-ResolvedFeatures"]),
            "refusals": refusals, "retained_policy_refusals": [*prior_operations, "raw_extraction"],
            "runtime_input_file_reads": len(audit.denied)}



def check_cli(root, request):
    body = request["document"]
    name = body["metadata"]["name"] + ".SLDPRT"
    bootstrap = """import sys
sys.path.insert(0, sys.argv.pop(1))
from convert.Commands.MainEntry import MainEntry
raise SystemExit(MainEntry())
"""
    with TemporaryDirectory(prefix="KitMeasuredPartCli-") as scratch:
        base = Path(scratch)
        source, target, receipt = base / "Neutral.json", base / name, base / "Evidence.json"
        source.write_text(json.dumps(body), encoding="utf-8")
        receipt.write_text(json.dumps(request["evidence"]), encoding="utf-8")
        target.write_bytes(b"prior output")
        command = [sys.executable, "-I", "-B", "-c", bootstrap, str(root / "src"), "convert",
                   str(source), str(target), "--json", "--overwrite"]
        denied = subprocess.run(command, capture_output=True, text=True, check=False, timeout=90)
        demand(denied.returncode == 1 and "offline native measurement receipt" in denied.stderr
               and target.read_bytes() == b"prior output", "CLI published unmeasured part bytes")
        old = subprocess.run([*command, "--allow-unverified-native"], capture_output=True, text=True, check=False, timeout=90)
        demand(old.returncode == 2 and "unrecognized arguments" in old.stderr and target.read_bytes() == b"prior output",
               "old candidate flag still reaches publication")
        if os.name == "nt":
            return {"accepted_host_path": False, "refusals": 2}
        measured = subprocess.run([*command, "--native-measurement", str(receipt)],
                                  capture_output=True, text=True, check=False, timeout=90)
        demand(measured.returncode == 0 and not measured.stderr, measured.stderr)
        result = json.loads(measured.stdout)
        demand(result["application_usable"] and result["vendor_loadable"] and not result["dropped"]
               and "caller supplied offline" in result["acceptance"]
               and digest(target.read_bytes()) == request["sha256"] and set(base.iterdir()) == {source, target, receipt},
               "CLI did not publish the exact measured file transaction")
        return {"accepted_host_path": True, "refusals": 2}


def supervise(root, directory, output):
    receipt_path = root / "re/solidworks/measurements/2026/SdkDefaultPartNative01.json"
    receipt_raw = receipt_path.read_bytes()
    receipt = json.loads(receipt_raw)
    written = check_custody(directory, receipt)
    results = []
    for build in receipt["builds"]:
        role = build["role"]
        exact_request = read_pinned(directory / role / "SdkRequest.json", build["request_sha256"])
        demand(exact_request["written_at"] == written, "measured candidate time differs")
        request = {**exact_request, "role": role, "sha256": build["candidate_sha256"],
                   "evidence": {"written_at": written, "receipt": receipt}}
        execution = subprocess.run([sys.executable, "-I", "-B", str(HERE), "--root", str(root), "--worker"],
                                   input=json.dumps(request), capture_output=True, text=True, check=False, timeout=90)
        demand(execution.returncode == 0 and not execution.stderr, execution.stderr)
        results.append(json.loads(execution.stdout) | {"cli": check_cli(root, request)})
    source = root / "src/convert/adapters/solidworks/Core/Writing"
    files = [source / "EmitNativeMut.py", *(source / "Measured").glob("*.py"),
             source.parent / "Preparation/CheckPartOpts.py", source.parent / "Preparation/PlanPartWrite.py"]
    cli_sources = root / "src/convert/Commands"
    files += [cli_sources / name for name in ("CliOptions.py", "ConvertArgs.py", "ConvertFile.py", "NativeMeasVals.py", "WriteReport.py")]
    report = {"schema": "kit.sw2026.measured-public-part-proof.v1", "results": results, "fresh_reader_writer_processes": len(results),
              "controls": 2, "native_launches": 0, "prior_native_lifetimes": receipt["distinct_native_processes"],
              "native_measurements": receipt["numeric_checks"], "archived_evidence_sha256": digest(receipt_raw),
              "terminal_sha256": receipt["native_result_sha256"], "method_sha256": digest(HERE.read_bytes()),
              "source_sha256": {path.relative_to(root).as_posix(): digest(path.read_bytes()) for path in sorted(files)}}
    with output.open("x") as stream:
        json.dump(report, stream, sort_keys=True, indent=2)
        stream.write("\n")
    print(json.dumps({"proof_sha256": digest(output.read_bytes()), "cases": len(results)}))


if __name__ == "__main__":
    cli = ArgumentParser()
    cli.add_argument("--root", type=Path, default=ROOT)
    cli.add_argument("--native", type=Path)
    cli.add_argument("--output", type=Path)
    cli.add_argument("--worker", action="store_true")
    options = cli.parse_args()
    if options.worker:
        with TemporaryDirectory(prefix="KitMeasuredPart-") as temp:
            print(json.dumps(worker(options.root, json.load(sys.stdin), Path(temp).resolve()), sort_keys=True))
    else:
        supervise(options.root, options.native, options.output)
