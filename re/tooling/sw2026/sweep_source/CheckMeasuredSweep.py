from argparse import ArgumentParser
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory


HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(HERE.parent)]
from ProveSdkSweepPart import expected_refusal, guard_runtime
from ProveSweepDocument import neutral_document
from ReplayHeldoutSweepSdk import inspect_part
from SweepMeasuredReceipt import PORTABLE, normalize
from SweepModel import dimensions, require
from convert import write_document
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.Adapter import SldprtAdapter
from convert.adapters.solidworks.Core.Preparation.PrepareNative import PrepareNative
from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
from interchange.serialization.JsonCodec import DumpJson, LoadJson


OPTION = "solidworks_native_measurement"
FORMAT = "solidworks.sldprt"


class Nonseekable(BytesIO):
    def seekable(self):
        return False


def registry(document, sink, values):
    return write_document(document, sink, destination_format=FORMAT, allow_carrier=True,
                          validate=False, values=values)


def adapter(document, sink, values):
    return SldprtAdapter().write(document, sink, WriteOptions(values=values))


def direct(document, sink, values):
    return SldprtWriter().write(document, sink, WriteOptions(values=values))


def sink_refusals(publish, document, options):
    for content, cursor, kind in (
        (b"existing suffix", 0, BytesIO), (b"existing prefix", 15, BytesIO),
        (b"", 24, BytesIO), (b"", 0, Nonseekable),
    ):
        sink = kind(content)
        sink.seek(cursor)
        expected_refusal(lambda: publish(document, sink, options), "empty seekable binary stream")
        require(sink.getvalue() == content and sink.tell() == cursor,
                "incompatible standalone sink was changed")
    return 4


def contrary_models(case, density, document):
    for role in ("section", "path"):
        yield role + "_edit_without_measurement", neutral_document(case["name"], *dimensions(case, role), density),             "no unique exact native measurement"
    sweep, = document.feature_timeline
    broken = replace(sweep, definition=replace(sweep.definition, PathSketchId=sweep.sketch_id))
    yield "crossed_profile", replace(document, feature_timeline=(broken,)), "distinct actual path sketch"


def contrasts(publish, document, request, values):
    slot = request["slot"]
    envelope = values[OPTION]
    options = {
        "missing_receipt": ({k: v for k, v in values.items() if k != OPTION}, "offline native measurement receipt"),
        "changed_epoch": (values | {OPTION: envelope | {"written_at": request["epoch"] + 1}}, "no unique exact native measurement"),
        "changed_locator": (values | {"final_destination": "C:\\Unmeasured\\" + request["case"]["name"] + ".SLDPRT"},
                            "no unique exact native measurement"),
    }
    for label, tamper, diagnostic in (
        ("foreign_build", lambda report: report["oracle"].update(build="34.0.0.0"), "exact passing SOLIDWORKS"),
        ("unhealthy_control", lambda report: report["phases"][0].update(solid_count=0), "both healthy bracket controls"),
        ("reused_lifetime", lambda report: report["phases"][1].update(lifetime=report["phases"][0]["lifetime"]),
         "repeats a process"),
        ("claimed_wrong_locator", lambda report: report["cases"][slot].update(locator="C:\\different.SLDPRT"), "scope or locator"),
        ("claimed_wrong_length", lambda report: report["cases"][slot].update(archive_bytes=1), "scope or locator"),
        ("claimed_wrong_archive", lambda report: report["cases"][slot].update(archive_sha256="d" * 64),
         "no unique exact native measurement"),
        ("wrong_saved_derivative", lambda report: report["cases"][slot].update(path_save_sha256="b" * 64),
         "exact native edits and saved reopens"),
        ("swapped_driver", lambda report: report["cases"][slot]["states"][0]["drivers"].reverse(),
         "two owned driving dimensions"),
        ("wrong_reported_dimension", lambda report: report["cases"][slot]["states"][0].update(path_radius_m=0.001),
         "both generated driving dimensions"),
        ("wrong_reopen_mass", lambda report: report["cases"][slot]["states"][4].update(mass_kg=3.0),
         "isolated edits and reopened body"),
        ("wrong_save_status", lambda report: report["cases"][slot].update(save_status=[[True, 0, 0], [True, 0, 1]]),
         "clean native driver edits or numeric coverage"),
        ("false_setter_codes", lambda report: report["cases"][slot].update(setter_status=[False, False]),
         "clean native driver edits or numeric coverage"),
        ("unbound_terminal", lambda report: report.update(native_result_sha256=report["trial_sha256"]),
         "authenticated offline evidence"),
        ("absent_independent_observer", lambda report: report["cases"][slot]["independent_observer_sha256"].pop("path"),
         "lacks the independent comparisons"),
        ("no_independent_comparison", lambda report: report["cases"][slot].update(paired_numeric_checks=0),
         "clean native driver edits or numeric coverage"),
    ):
        changed = deepcopy(envelope)
        tamper(changed["receipt"])
        options[label] = values | {OPTION: changed}, diagnostic
    models = {label: (document, settings, diagnostic) for label, (settings, diagnostic) in options.items()}
    for label, model, diagnostic in contrary_models(request["case"], request["density"], document):
        if label != "crossed_profile" or publish is not registry:
            models[label] = model, values, diagnostic
    for model, settings, diagnostic in models.values():
        sink = BytesIO()
        expected_refusal(lambda: publish(model, sink, settings), diagnostic)
        require(not sink.getvalue() and sink.tell() == 0, "refused sweep changed the caller's sink")
    return {"refusals": list(models), "incompatible_streams": sink_refusals(publish, document, values)}


def check_paths(document, locator, envelope):
    with TemporaryDirectory(prefix="KitMeasuredSweepPath-") as directory:
        root = Path(directory)
        target = root / (document.metadata["name"] + ".SLDPRT")
        sentinel = b"existing caller part"
        target.write_bytes(sentinel)
        for settings, diagnostic in (
            ({}, "offline native measurement receipt"),
            ({OPTION: envelope}, "no unique exact native measurement"),
            ({OPTION: envelope, "final_destination": locator}, "no unique exact native measurement"),
        ):
            expected_refusal(lambda: write_document(document, target, overwrite=True, allow_carrier=True,
                                                     validate=False, values=settings), diagnostic)
            require(target.read_bytes() == sentinel and tuple(root.iterdir()) == (target,),
                    "denied filesystem sweep changed its existing final path or left staging")
        values = {OPTION: envelope, "final_destination": locator}
        expected_refusal(lambda: SldprtWriter().write(document, target, WriteOptions(overwrite=True, values=values)),
                         "actual final filesystem locator")
        require(target.read_bytes() == sentinel and tuple(root.iterdir()) == (target,),
                "foreign explicit locator changed the direct filesystem destination")
    return 4


def worker(request):
    case, density = request["case"], request["density"]
    radii = dimensions(case)
    model = neutral_document(case["name"], *radii, density)
    model_json = request["neutral"]
    document = LoadJson(model_json)
    proof = request["portable"]
    historical = json.loads(model_json)
    (feature,) = historical["feature_timeline"]["$tuple"]
    require(feature.pop("output_body_ids") == {"$tuple": []}, "the disclosed sweep has an unexpected authored output link")
    require(DumpJson(model) == model_json == DumpJson(document)
            and sha256(DumpJson(historical).encode()).hexdigest() == proof["json_sha256"],
            "neutral SDK model is not the independently measured portable input")
    locator, epoch, envelope = request["locator"], request["epoch"], request["evidence"]
    counts = check_paths(document, locator, envelope)
    blocked = guard_runtime()
    candidate = PrepareNative(document, BytesIO(), epoch, WriteOptions(values={"final_destination": locator}))
    linked_streams = list(inspect_part(candidate, radii))
    stream_hashes = {name: sha256(payload).hexdigest() for name, payload in candidate.StreamsValue.items()}
    map_counts = [graph.MapValue.CounterValue for graph in (candidate.ConfigValue, candidate.ResolvedValue)]
    digest = proof["candidate_sha256"]
    require(sha256(candidate.BytesValue).hexdigest() == request["expected_sha256"] == digest
            and stream_hashes == proof["stream_sha256"]
            and linked_streams == proof["comparison_streams"]
            and map_counts == proof["map_counts"],
            "prepared output differs from the measured Standard sweep archive or linked owners")
    values = {"final_destination": locator, OPTION: envelope}
    checked = {}
    for publish in (registry, adapter, direct):
        sink = BytesIO()
        result = publish(document, sink, values)
        evidence = result.metadata[OPTION]
        require(sink.getvalue() == candidate.BytesValue and sink.tell() == result.bytes_written == len(candidate.BytesValue)
                and result.application_usable and result.vendor_loadable and not result.dropped
                and evidence["generated_sha256"] == digest and len(evidence["phase_record_sha256"]) == 5,
                "public output did not retain full exact archive and native qualification")
        if publish is not adapter:
            checked[publish.__name__] = contrasts(publish, document, request, values)
    require(not blocked and not any(name.startswith(("pythoncom", "win32com")) for name in sys.modules),
            "sweep writer used external files, processes or the CAD runtime")
    return {"case": case["name"], "archive_sha256": digest, "streams": len(candidate.StreamsValue),
            "linked_streams": linked_streams, "scope": ["registry", "adapter", "direct"],
            "native_posix_path_refusals": counts, "guarded_contrasts": checked, "runtime_external_calls": len(blocked)}


def write_json(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    return sha256(path.read_bytes()).hexdigest()


def supervise(native, output, receipt_output):
    receipt, requests = normalize(native)
    results = []
    for row, request in zip(receipt["cases"], requests, strict=True):
        case = request["case"]
        request |= {"slot": row["slot"], "epoch": row["written_at"], "locator": row["locator"],
                    "expected_sha256": row["archive_sha256"], "evidence": {"written_at": row["written_at"], "receipt": receipt},
                    "neutral": DumpJson(neutral_document(case["name"], *dimensions(case), request["density"]))}
        run = subprocess.run([sys.executable, "-I", "-B", str(HERE), "--worker"],
                             input=json.dumps(request), capture_output=True, text=True, check=False, timeout=90)
        require(run.returncode == 0 and not run.stderr, run.stderr)
        results.append(json.loads(run.stdout))
    adapters = ROOT / "src/convert/adapters"
    core = adapters / "solidworks/Core"
    source = [*sorted((core / "Preparation/Sweeps").glob("*.py")), *sorted((core / "Writing/Sweeps").glob("*.py")),
              *sorted((core / "Writing/Measured").glob("*.py")), core / "Preparation/PrepareNative.py",
              *(core / "Writing" / f"{name}.py" for name in ("CanWritePart", "CanWriteSweep", "EmitNativeMut", "SldprtWriter")),
              adapters / "base/WholeStreamWriter.py", *(adapters / "Staging" / f"{name}.py"
                  for name in ("StreamStaging", "CheckWholeSink", "SeekBinary", "SinkExtentMut", "WriteWholeMut"))]
    print(write_json(output, {
        "schema": "kit.sw2026.measured-standard-sweep-publication-proof.v1",
        "guarded_processes": len(results), "results": results,
        "native_source_processes": receipt["fresh_processes"], "native_launches": 0, "heldout_credit": 0,
        "native_phase_checks": sum(phase["checks"] for phase in receipt["phases"]),
        "independent_numeric_checks": sum(case["paired_numeric_checks"] for case in receipt["cases"]),
        "disclosed_native_result_sha256": receipt["native_result_sha256"], "portable_proof_sha256": PORTABLE,
        "normalized_receipt_sha256": write_json(receipt_output, receipt),
        "src_sha256": {path.relative_to(ROOT).as_posix(): sha256(path.read_bytes()).hexdigest() for path in sorted(source)},
        "method": {path.name: sha256(path.read_bytes()).hexdigest() for path in (HERE, HERE.with_name("SweepMeasuredReceipt.py"))},
    }))


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--native", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(worker(json.load(sys.stdin)), sort_keys=True, allow_nan=False))
    else:
        supervise(args.native, args.output, args.receipt)
