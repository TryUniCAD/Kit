from argparse import ArgumentParser
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path, PureWindowsPath
import subprocess
import sys
from tempfile import TemporaryDirectory

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
FORMAT = "solidworks.sldprt"
OPTION = "solidworks_native_measurement"
AUTHORITY = "b50eb4668453ab4698f9bed0289809ba347b43a78c580a0646b8c3e0f3b6be38"
REPORT = ROOT / "re/solidworks/measurements/2026/AttachedTopBoxHeldoutNative01.json"
METHOD = "kit.sw2026.exact-top-box-publication.v1"


def launch_args():
    sys.path[:0] = [str(ROOT / "src"), str(HERE.parent), str(HERE.parent.parent)]
    from ProveTopCornerPublic import warm

    warm()
    lookup("cp1252")


def values(locator, epoch, report):
    return {
        "final_destination": locator,
        "require_native_transfers": True,
        OPTION: {"written_at": epoch, "receipt": report},
    }


def routes():
    from convert import write_document
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.solidworks.Core.Adapter import SldprtAdapter
    from convert.api.ApiContext import GetRegistry

    writer = GetRegistry().GetWriter(FORMAT)
    adapter = SldprtAdapter()
    return {
        "registry": lambda model, sink, settings: write_document(
            model, sink, destination_format=FORMAT, allow_carrier=False, values=settings
        ),
        "adapter": lambda model, sink, settings: adapter.write(
            model, sink, WriteOptions(values=settings)
        ),
        "writer": lambda model, sink, settings: writer.write(
            model, sink, WriteOptions(values=settings)
        ),
    }


def refuse(callback, expected):
    try:
        callback()
    except ValueError as error:
        if expected not in str(error):
            raise
    else:
        raise ValueError("unqualified Top part reached the output")


def positive(result, expected, report, slot, model):
    from convert.adapters.base.GetDocumentCaps import GetDocumentCaps

    proof = result.metadata[OPTION]
    phases = {row["name"]: row["record_sha256"] for row in report["phases"]}
    assert result.vendor_loadable and result.application_usable
    assert result.bytes_written == expected["bytes"]
    assert not result.dropped and not result.carrier_capabilities
    assert GetDocumentCaps(model) <= result.native_capabilities
    assert all(row.mode.value == "native" for row in result.transfers)
    assert proof["authority_sha256"] == AUTHORITY and proof["qualified_slot"] == slot
    assert proof["generated_sha256"] == expected["sha256"]
    assert proof["native_result_sha256"] == report["job_result_sha256"]
    assert proof["oracle_build"] == "34.5.2.0604"
    assert proof["edit_record_sha256"] == phases[slot + "Edit"]
    assert proof["reopen_record_sha256"] == phases[slot + "Reopen"]


def run_staged(model, settings, locator, report, slot):
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.Staging.StageFileScope import StageFileScope
    from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
    from VerifySdkCircleEndRegistration import OutputGuard

    writer = SldprtWriter()
    target = Path(locator)
    expected = report["cases"][slot]["build"]
    with TemporaryDirectory(dir=target.parent, prefix=f".{target.name}.kit-") as scratch:
        stage = Path(scratch) / target.name
        guard = OutputGuard(Path(scratch), target.name)
        sys.addaudithook(guard.audit)
        with StageFileScope(stage, target), guard.active("path"):
            result = writer.write(model, stage, WriteOptions(values=settings))
        positive(result, expected, report, slot, model)
        assert result.path == stage and sha256(stage.read_bytes()).hexdigest() == expected["sha256"]
        assert guard.events["open"] == 1 and not guard.denied


def worker(request):
    launch_args()
    from convert import open_document
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.Preparation.FreecadBox.Readback.ReadTopInput import ReadTopInput
    from interchange import CadDocument
    from VerifySdkCircleEndRegistration import OutputGuard

    report = request["receipt"]
    slot = request["slot"]
    expected = report["cases"][slot]["build"]
    locator = request["locator"]
    epoch = request["epoch"]
    model = CadDocument.from_json(request["document"])
    expected_settings = values(locator, epoch, report)
    name = PureWindowsPath(locator).stem
    active_routes = routes()
    audit = OutputGuard(HERE.parent, name + ".SLDPRT")
    sys.addaudithook(audit.audit)
    matching = 0
    with audit.active("memory"):
        neutral = ReadTopInput(model, name)
        for variant in (model, neutral):
            for emit in active_routes.values():
                sink = BytesIO()
                result = emit(variant, sink, expected_settings)
                positive(result, expected, report, slot, variant)
                payload = sink.getvalue()
                assert sha256(payload).hexdigest() == expected["sha256"]
                streams = SldprtArchive.from_bytes(payload).streams
                assert {k: {"bytes": len(v), "sha256": sha256(v).hexdigest()}
                        for k, v in streams.items()} == expected["streams"]
                assert open_document(BytesIO(payload), source_format=FORMAT, strict=True).to_json() == model.to_json()
                matching += 1
        wrong = {**expected_settings, OPTION: {"written_at": epoch + 1, "receipt": report}}
        sink = BytesIO(b"preserved")
        refuse(lambda: active_routes["writer"](neutral, sink, wrong), "no exact held-out native measurement")
        assert sink.getvalue() == b"preserved" and sink.tell() == 0
    run_staged(model, expected_settings, locator, report, slot)
    assert not audit.denied
    return {"slot": slot, "archive_sha256": expected["sha256"], "exact_streams": len(expected["streams"]),
            "exact_guarded_stream_publications": matching, "exact_guarded_file_stage_writes": 1,
            "clock_refused_without_output": True, "runtime_input_reads": 0}


def host():
    launch_args()
    from convert import open_document
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.solidworks.Core.Preparation.FreecadBox.PrepTopPart import PrepTopPart
    from ProveTopCornerPublic import payload
    from VerifyColdTopBox import CASES, EPOCH, LOCATOR, make_document
    from VerifySdkCircleEndRegistration import OutputGuard

    report = json.loads(payload(REPORT, AUTHORITY))
    document = make_document(CASES[1])
    active_routes = routes()
    settings = values(LOCATOR, EPOCH, report)
    bad_report = {**report, "controls_healthy": False}
    bad = values(LOCATOR, EPOCH, bad_report)
    guard = OutputGuard(HERE.parent, "SignedBox.SLDPRT")
    sys.addaudithook(guard.audit)
    wrong = BytesIO(b"prior")
    with guard.active("memory"):
        candidate = PrepTopPart(
            document, BytesIO(), EPOCH, WriteOptions(values={"final_destination": LOCATOR}),
            PlatformMath=True,
        )
        forged = json.loads(json.dumps(report))
        forged["cases"]["Slot01"]["build"].update(
            sha256=sha256(candidate.BytesValue).hexdigest(),
            bytes=len(candidate.BytesValue),
            streams={name: {"bytes": len(raw), "sha256": sha256(raw).hexdigest()}
                     for name, raw in candidate.StreamsValue.items()},
        )
        forged_values = values(LOCATOR, EPOCH, forged)
        readback = open_document(candidate.BytesValue, source_format=FORMAT, strict=True)
        for emit in active_routes.values():
            refuse(lambda: emit(document, wrong, bad), "authenticated held-out evidence")
            refuse(lambda: emit(document, wrong, forged_values), "authenticated held-out evidence")
            refuse(lambda: emit(document, wrong, settings), "no exact held-out native measurement")
            refuse(lambda: emit(readback, wrong, settings), "no exact held-out native measurement")
    assert not guard.denied and wrong.getvalue() == b"prior" and wrong.tell() == 0
    return {"schema": METHOD, "native_processes_started": 0, "refused_stream_publications": 12,
            "measured_reports_used": 1, "runtime_input_reads": 0}


def source_manifest():
    prefix = ROOT / "src/convert/adapters/solidworks/Core"
    paths = (prefix / "Preparation/FreecadBox/PrepTopPart.py",
             prefix / "Preparation/FreecadBox/Readback/IsTopRead.py",
             prefix / "Preparation/FreecadBox/Readback/PrepColdTop.py",
             prefix / "Writing/CanWritePart.py", prefix / "Writing/EmitNativeMut.py",
             *(prefix / "Writing/TopBoxes" / part for part in
               ("EmitTopMeasMut.py", "MatchTopMeas.py", "ReadTopMeas.py")))
    return {path.relative_to(ROOT).as_posix(): sha256(path.read_bytes()).hexdigest()
            for path in paths}


def compare(prior, output):
    if sys.platform != "win32":
        raise ValueError("the retained generated comparison is guest-only")
    launch_args()
    from convert import open_document
    from ProveTopCornerPublic import PRIOR_JOB, PRIOR_RESULT, SLOTS, payload

    report = json.loads(payload(REPORT, AUTHORITY))
    job = json.loads(payload(prior / "Job.json", PRIOR_JOB))
    terminal = json.loads(payload(prior / "Result.json", PRIOR_RESULT))
    assert report["job_result_sha256"] == PRIOR_RESULT and report["job_sha256"] == PRIOR_JOB
    assert terminal["passed"] and terminal["controls_healthy"] and terminal["distinct_processes"] == 6
    assert terminal["job_sha256"] == PRIOR_JOB and terminal["heldout_candidates_passed"] == len(SLOTS)
    target = Path(job["target"])
    assert target.resolve(strict=True) == target and target.drive == "C:" and not target.is_symlink()
    outcomes = []
    for slot in SLOTS:
        known = report["cases"][slot]["build"]
        terminal_row = terminal["cases"][slot]["build"]
        assert all(known[key] == terminal_row[key] for key in ("sha256", "bytes", "streams"))
        path = target / slot / "SignedBox.SLDPRT"
        assert path.resolve(strict=True) == path and not path.is_symlink()
        raw = payload(path, known["sha256"])
        document = open_document(BytesIO(raw), source_format=FORMAT, strict=True)
        request = {"slot": slot, "document": document.to_json(), "epoch": job["creation_epoch"],
                   "locator": str(path), "receipt": report}
        process = subprocess.run(
            (sys.executable, "-I", "-B", str(HERE), "worker"),
            input=json.dumps(request), capture_output=True, text=True, check=False, timeout=120,
        )
        if process.returncode or process.stderr:
            raise ValueError(f"{slot} publication verification failed")
        outcomes.append(json.loads(process.stdout))
        assert payload(path, known["sha256"]) == raw
    public = {"schema": METHOD, "cases": outcomes, "native_processes_started": 0,
              "original_native_sources_read": 0, "qualification_receipt_sha256": AUTHORITY,
              "prior_native_result_sha256": PRIOR_RESULT, "method_sha256": sha256(HERE.read_bytes()).hexdigest(),
              "source_manifest_sha256": source_manifest()}
    raw = (json.dumps(public, indent=2, sort_keys=True) + "\n").encode()
    with output.open("xb") as handle:
        handle.write(raw)
    return {"receipt_sha256": sha256(raw).hexdigest(), "verified_slots": len(outcomes)}


def main():
    parser = ArgumentParser()
    modes = parser.add_subparsers(dest="mode", required=True)
    modes.add_parser("host")
    modes.add_parser("worker")
    guest = modes.add_parser("compare")
    guest.add_argument("prior", type=Path)
    guest.add_argument("output", type=Path)
    options = parser.parse_args()
    if options.mode == "host":
        result = host()
    elif options.mode == "worker":
        result = worker(json.load(sys.stdin))
    else:
        result = compare(options.prior, options.output)
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
