from argparse import ArgumentParser
from codecs import lookup
from copy import deepcopy
from dataclasses import replace
from io import BytesIO
from importlib import import_module
import json
from math import inf, nextafter
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))

from ProvePairRead import (FORMAT, GENERATED, PAIRS, ROOT, TRIAL_SHA, digest, expected_pair,
                           pair_geometry, pinned, read_doc, reject, require)
from ProvePublicChamferWrite import EPOCH, authored
from VerifySdkCircleEndRegistration import OutputGuard
from convert import write_document
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Archive.Construction.Views.ViewPlans import KViewPlans
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Preparation.Chamfers.PrepChmfPart import PrepChmfPart
from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
from interchange.document.Models.DocumentModel import CadDocument

OPTION = "solidworks_native_measurement"
SCHEMA = "kit.sw2026.distance-pair-publication.v1"
NATIVE_PIN = "6538bdc0dfa5d1b82fab03bde1d742f98fabd8c9299c1a18c2e55f5248b429c9"
RUNNER_PIN = "9c331a7e6a8fa43dc483587d0447aeb27e11fe988c715079396a683f87b6a156"
ANGLE_PIN = "d161909999b3ed8d72f0885dbb6dbc0dfa3866e712dc4dd390aef7406c236409"


def canonical(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def evidence(compiled, native):
    generated_raw = pinned(compiled / "Generated.json", GENERATED)
    native_raw = pinned(native, NATIVE_PIN)
    _ = pinned(compiled / "RunPairCandidates.py", RUNNER_PIN)
    generation, terminal = (json.loads(raw) for raw in (generated_raw, native_raw))
    require(canonical(generation) == generated_raw and canonical(terminal) == native_raw
            and terminal["generation_sha256"] == GENERATED and terminal["runner_sha256"] == RUNNER_PIN,
            "measured runner and reports have different authority")
    return {"written_at": generation["written_at"],
            "receipt": {"schema": SCHEMA, "generation": generation,
                        "native_result": terminal, "native_result_sha256": NATIVE_PIN}}


def publish(document, target, options, direct, *, overwrite=False):
    if direct:
        return SldprtWriter().write(document, target, WriteOptions(overwrite=overwrite, values=options))
    return write_document(document, target, destination_format=FORMAT, allow_carrier=False,
                          overwrite=overwrite, values=options)


def verify_flags(result, payload, archive_sha, phase_pins):
    meta = result.metadata[OPTION]
    require(result.application_usable and result.vendor_loadable and not result.dropped
            and result.bytes_written == len(payload) and not result.carrier_capabilities
            and meta["generated_sha256"] == archive_sha and meta["native_result_sha256"] == NATIVE_PIN
            and meta["generation_sha256"] == GENERATED and tuple(meta["phase_record_sha256"]) == phase_pins,
            "published result did not attest that exact measured lifecycle")


def recertify(envelope, *changes):
    result = deepcopy(envelope)
    receipt = result["receipt"]
    terminal = receipt["native_result"]
    generation = receipt["generation"]
    for change in changes:
        change(generation, terminal)
    terminal["generation_sha256"] = digest(canonical(generation))
    receipt["native_result_sha256"] = digest(canonical(terminal))
    return result


def changed_distance(document):
    stock, step = document.feature_timeline
    distance_id = step.parameter_ids[0]
    new_value = replace(step.definition.distance, value=step.definition.distance.value + 0.125)
    params = tuple(replace(item, value=new_value) if item.id == distance_id else item
                   for item in document.parameters)
    return replace(document, parameters=params, feature_timeline=(
        stock, replace(step, definition=replace(step.definition, distance=new_value))))


def write_refusals(document, envelope, locator):
    raw = b"preserve caller stream"
    base = {"final_destination": locator, "require_native_transfers": True}
    exact = base | {OPTION: envelope}
    prefix = "regenerated distance chamfer has no unique exact native measurement"
    wrong_scope = lambda generation, _: generation.update(destination=r"C:\DifferentPacket")
    bad_control = lambda _, terminal: terminal["controls"][0].update(passed=False)
    duplicate = lambda _, terminal: terminal["candidates"][0]["phases"][0].update(
        record_sha256=terminal["controls"][0]["record_sha256"])
    bad_phase = lambda _, terminal: terminal["candidates"][1]["phases"][1].update(checks=21)
    bad_driver = lambda _, terminal: terminal["candidates"][1]["drivers"].update(
        second=["D2", "DistancePairEdgeChamfer", 2, 0])
    cases = {
        "missing_report": (document, base, "offline native measurement receipt"),
        "different_epoch": (document, exact | {OPTION: envelope | {"written_at": envelope["written_at"] + 1}},
                            "does not match its exact oracle batch"),
        "different_locator": (document, exact | {"final_destination": r"C:\DifferentPacket\\" + locator.rsplit("\\", 1)[1]}, prefix),
        "different_model": (changed_distance(document), exact, prefix),
        "failed_control": (document, exact | {OPTION: recertify(envelope, bad_control)}, "failed or unowned phase"),
        "duplicate_phase": (document, exact | {OPTION: recertify(envelope, duplicate)}, "repeats or omits a native phase"),
        "changed_check_count": (document, exact | {OPTION: recertify(envelope, bad_phase)}, "failed or unowned phase"),
        "mislabeled_receipt_locator": (document, exact | {OPTION: recertify(envelope, wrong_scope)},
                                      "does not match its generated scope or locator"),
    }
    if document.feature_timeline[-1].definition.mode == "two_distances":
        cases["different_driver"] = (document, exact | {OPTION: recertify(envelope, bad_driver)}, "unowned driver")
    unbound = recertify(envelope, lambda _, terminal: terminal.update(method_sha256=terminal["runner_sha256"]))
    cases["unbound_terminal"] = (document, exact | {OPTION: unbound}, "authenticated offline evidence")
    failed_hash = deepcopy(envelope)
    failed_hash["receipt"]["native_result_sha256"] = "f" * 64
    cases["wrong_terminal_digest"] = (document, exact | {OPTION: failed_hash}, "does not match its exact oracle batch")
    for direct in (False, True):
        for model, options, diagnostic in cases.values():
            output = BytesIO(raw)
            output.seek(5)
            reject(lambda: publish(model, output, options, direct), diagnostic)
            require(output.getvalue() == raw and output.tell() == 5,
                    "failed measured request changed a caller stream")
        occupied = BytesIO(raw)
        reject(lambda: publish(document, occupied, exact, direct), "empty")
        require(occupied.getvalue() == raw and occupied.tell() == 0,
                "qualified write changed an occupied standalone stream")
    return [*cases, "occupied_stream"]


def warm_modules():
    for codec in ("ascii", "latin-1", "utf-8", "utf-8-sig", "utf-16-le", "utf-16-be", "cp1252"):
        lookup(codec)
    for module in ("interchange.brep.Validation.BrepValidate", "interchange.document.Behavior.DocumentIo",
                   "interchange.document.Models.DocumentProvenance", "interchange.document.Validation.DocumentValidate",
                   "interchange.document.Validation.DocumentAssemblyValidate", "interchange.document.Validation.DocumentFeatureValidate",
                   "interchange.document.Validation.DocumentReferenceValidate"):
        import_module(module)


def signed_control(payload):
    control = payload["angle_control"]
    document = authored(control["case"], control["side"])
    options = {"final_destination": control["locator"],
               OPTION: {"written_at": EPOCH, "receipt": control["receipt"]}}
    for direct in (False, True):
        output = BytesIO()
        result = publish(document, output, options, direct)
        require(digest(output.getvalue()) == control["expected_sha256"]
                and result.vendor_loadable and result.application_usable
                and result.metadata[OPTION]["native_result_sha256"] == ANGLE_PIN,
                "exact signed angle control changed under measured dispatch")
    return control["expected_sha256"]


def camera_contrast(document, options, exact, request):
    views = import_module("convert.adapters.solidworks.Archive.Construction.Views.MakeStdViews")
    original = views.ViewRotation
    quarter_turn = abs(KViewPlans[3][1][0][1])

    def adjacent(axis, angle, *, PlatformMath=False):
        x, y, z, cosine = original(axis, angle, PlatformMath=PlatformMath)
        return (x, y, z, nextafter(cosine, inf)) if abs(angle) == quarter_turn else (x, y, z, cosine)

    views.ViewRotation = adjacent
    try:
        typed = PrepChmfPart(document, BytesIO(), request["epoch"],
                             WriteOptions(values={"final_destination": request["locator"]}),
                             AllowDistancePair=True)
        original_archive = SldprtArchive.from_bytes(exact)
        difference = [name for name, stream in typed.StreamsValue.items() if original_archive.require(name) != stream]
        require(difference == ["Contents/Config-0"] and typed.BytesValue != exact,
                "adjacent camera control changed unrelated archive streams")
        unchanged = BytesIO(b"preserve when the measured hash differs")
        reject(lambda: publish(document, unchanged, options, False),
               "regenerated distance chamfer has no unique exact native measurement")
        require(unchanged.getvalue() == b"preserve when the measured hash differs" and unchanged.tell() == 0,
                "camera rounding contrast crossed the measured output gate")
    finally:
        views.ViewRotation = original
    return {"archive_sha256": digest(typed.BytesValue), "changed_streams": difference, "published": False}


def worker(payload):
    envelope = payload["envelope"]
    request = payload["request"]
    case = envelope["receipt"]["native_result"]["candidates"][payload["slot"]]
    phase_pins = tuple(item["record_sha256"] for item in case["phases"])
    document = CadDocument.from_json(json.dumps(request["document"]))
    host_path = Path(payload["host_path"])
    options = {"final_destination": request["locator"], "require_native_transfers": True, OPTION: envelope}
    warm_modules()
    audit = OutputGuard(host_path.parent, host_path.name)

    def observe(event, details):
        if audit.mode is not None and event.startswith(("socket.", "winreg.")):
            audit.denied_event(event, details)
        if audit.mode == "path" and event == "open":
            target = audit.event_path(details[0])
            if target is None or not target.is_dir():
                audit.denied_event(event, details)
        audit.audit(event, details)

    sys.addaudithook(observe)
    outputs = []
    with audit.active("memory"):
        for direct in (False, True):
            target = BytesIO()
            status = publish(document, target, options, direct)
            data = target.getvalue()
            require(digest(data) == case["candidate_sha256"], "regenerated measured bytes differ")
            verify_flags(status, data, case["candidate_sha256"], phase_pins)
            outputs.append(data)
        require(outputs[0] == outputs[1], "measured stream routes differ")
        expected, _, _, primary = expected_pair(document)
        geometry = pair_geometry(read_doc(outputs[0], True), expected, primary)
        negatives = write_refusals(document, envelope, request["locator"])
        angle_hash = signed_control(payload) if "angle_control" in payload else None
        camera = camera_contrast(document, options, outputs[0], request)
    with audit.active("path"):
        for direct in (False, True):
            reject(lambda: publish(document, host_path, {OPTION: envelope}, direct, overwrite=True),
                   "regenerated distance chamfer has no unique exact native measurement")
    require(not audit.denied and not any(name.startswith(("pythoncom", "win32com")) for name in sys.modules),
            "measurement writer crossed the runtime input boundary")
    return {"slot": payload["slot"], "mode": document.feature_timeline[-1].definition.mode,
            "archive_sha256": case["candidate_sha256"], "bytes": len(outputs[0]), "locator": request["locator"],
            "phase_sha256": phase_pins, "native_phase_checks": [item["checks"] for item in case["phases"]],
            "registry_and_direct_measured_streams": 2, "runtime_reads": len(audit.denied),
            "preserved_signed_control": angle_hash, "refusals_by_route": [*negatives, "different_host_path"],
            "strict_geometry": geometry, "adjacent_camera_refusal": camera}


def supervise(args):
    envelope = evidence(args.compiled, args.native)
    trial = json.loads(pinned(args.signed_trial, TRIAL_SHA))
    angle_terminal = json.loads(pinned(ROOT / "re/solidworks/measurements/2026/ChamferSignedSideNative01.json", ANGLE_PIN))
    angle = trial["cases"][0]
    results = []
    with TemporaryDirectory(prefix="KitMeasuredPair-") as name:
        root = Path(name).resolve()
        for slot, (role, name, archive_pin, neutral_pin, mode) in enumerate(PAIRS):
            row = envelope["receipt"]["generation"]["candidates"][slot]
            request = json.loads(pinned(args.compiled / (role + "Neutral.json"), neutral_pin))
            require((name, archive_pin, neutral_pin, mode) ==
                    (row["name"], row["archive_sha256"], row["neutral_sha256"], row["mode_word"])
                    and request["locator"] == envelope["receipt"]["generation"]["destination"] + "\\" + name
                    and request["epoch"] == envelope["written_at"],
                    "disclosed measured case differs")
            folder = root / role
            folder.mkdir()
            target = folder / name
            original = b"preserve final file"
            target.write_bytes(original)
            payload = {"envelope": envelope, "request": request, "slot": slot, "host_path": str(target)}
            if slot == 0:
                payload["angle_control"] = {"case": trial["spec"]["cases"][0], "side": angle["branch"][0],
                                            "locator": angle["locator"], "expected_sha256": angle["archive_sha256"],
                                            "receipt": {"trial": trial, "native_result": angle_terminal}}
            result = subprocess.run([sys.executable, "-I", "-B", str(HERE), "--worker"],
                                    input=json.dumps(payload), capture_output=True, text=True, timeout=90, check=False)
            require(result.returncode == 0 and not result.stderr, result.stderr + result.stdout)
            require(set(folder.iterdir()) == {target} and target.read_bytes() == original,
                    "a refused path write changed the final target or left a staging artifact")
            results.append(json.loads(result.stdout))
    core = ROOT / "src/convert/adapters/solidworks/Core"
    writer = core / "Writing"
    sources = {HERE, HERE.parent / "ProvePairRead.py", HERE.parents[2] / "VerifySdkCircleEndRegistration.py",
               *sorted((writer / "Chamfers").glob("*.py")),
               *(writer / name for name in ("CanWritePart.py", "EmitNativeMut.py", "SldprtWriter.py")),
               core / "Preparation/Chamfers/IsDistChmf.py"}
    report = {"schema": "kit.sw2026.measured-distance-chamfer-publication-proof.v1",
              "generation_sha256": GENERATED, "native_result_sha256": NATIVE_PIN,
              "runner_sha256": RUNNER_PIN, "native_processes_started": 0, "prior_native_lifetimes": 6,
              "prior_healthy_controls": 2, "written_at": envelope["written_at"], "results": results,
              "fresh_guarded_workers": len(results), "source_sha256": {
                  path.relative_to(ROOT).as_posix(): digest(path.read_bytes()) for path in sorted(sources)}}
    with args.output.open("xb") as target:
        target.write(canonical(report))
    if args.envelope is not None:
        with args.envelope.open("xb") as target:
            target.write(canonical(envelope))
    print(digest(args.output.read_bytes()))


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--compiled", type=Path)
    parser.add_argument("--native", type=Path)
    parser.add_argument("--signed-trial", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--envelope", type=Path)
    parser.add_argument("--worker", action="store_true")
    options = parser.parse_args()
    if options.worker:
        print(json.dumps(worker(json.load(sys.stdin)), sort_keys=True))
    elif not all((options.compiled, options.native, options.signed_trial, options.output)):
        parser.error("provide compiled and native reports, signed control trial, and a fresh output")
    else:
        supervise(options)
