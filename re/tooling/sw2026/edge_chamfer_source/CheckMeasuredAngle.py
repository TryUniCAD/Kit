from argparse import ArgumentParser
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
from io import BytesIO
from json import dumps, loads
from pathlib import Path, PureWindowsPath
from platform import python_version
from subprocess import run
from tempfile import TemporaryDirectory
import sys
import zlib

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(HERE.parent), str(HERE.parent / "distance_pair")]

from CheckMeasuredPair import warm_modules
from ProvePublicChamferRead import physical, semantic
from ProvePublicChamferWrite import EPOCH, authored, typed
from VerifySdkCircleEndRegistration import OutputGuard
from convert import open_document, write_document
from convert.adapters.base.GetDocumentCaps import GetDocumentCaps
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Adapter import SldprtAdapter
from convert.adapters.solidworks.Core.Preparation.Chamfers.PrepChmfPart import PrepChmfPart
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ReadChmfOwn import ReadChmfOwn
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter


BASE = "6d85ed1cb9ff6c033c5a0017dbfc49ffb52bc146"
TRIAL = "8db08a479cd2b3e29dd4d5ad38eec3e96631e0aec15f71868a37aea51d423f49"
NATIVE = "d161909999b3ed8d72f0885dbb6dbc0dfa3866e712dc4dd390aef7406c236409"
HELDOUT = "3d6edf10c82b6140b2d08d470b9d242dee606dee83cacce51fbea46457d690e4"
RESULT = ROOT / "re/solidworks/measurements/2026"
FORMAT = "solidworks.sldprt"
MEASURE = "solidworks_native_measurement"


def digest(data):
    return sha256(data).hexdigest()


def canonical(data):
    return (dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def locked(path, checksum):
    data = path.read_bytes()
    assert digest(data) == checksum
    result = loads(data)
    assert canonical(result) == data
    return result


def registry(document, target, values, overwrite=False):
    return write_document(document, target, destination_format=FORMAT, allow_carrier=False,
                          values=values, overwrite=overwrite)


def adapter(document, target, values, overwrite=False):
    return SldprtAdapter().write(document, target, WriteOptions(values=values, overwrite=overwrite))


def writer(document, target, values, overwrite=False):
    return SldprtWriter().write(document, target, WriteOptions(values=values, overwrite=overwrite))


ROUTES = registry, adapter, writer


def reject(action, message):
    try:
        action()
    except ValueError as error:
        assert message in str(error), (message, str(error))
    else:
        raise AssertionError("unqualified chamfer published")


def edited(document, role):
    stock, chamfer = document.feature_timeline
    index, delta = {"distance": (0, 0.125), "angle": (1, 2.0)}[role]
    wanted = chamfer.parameter_ids[index]
    driver = next(row for row in document.parameters if row.id == wanted)
    value = replace(driver.value, value=driver.value.value + delta)
    params = tuple(replace(row, value=value) if row.id == wanted else row for row in document.parameters)
    definition = replace(chamfer.definition, **{role: value})
    return replace(document, parameters=params, feature_timeline=(stock, replace(chamfer, definition=definition)))


def contrasts(document, values):
    envelope = values[MEASURE]
    unmeasured = {name: value for name, value in values.items() if name != MEASURE}
    stale = values | {MEASURE: envelope | {"written_at": envelope["written_at"] + 1}}
    wrong_locator = values | {"final_destination": values["final_destination"].replace("Candidates", "Other")}
    unauthorized = deepcopy(envelope)
    unauthorized["receipt"]["native_result"]["healthy_controls"] = False
    forged = deepcopy(envelope)
    forged["receipt"]["trial"]["cases"][0]["archive_sha256"] = "0" * 64
    forged["receipt"]["native_result"]["manifest_sha256"] = digest(canonical(forged["receipt"]["trial"]))
    generic = envelope | {"receipt": {"schema": "kit.sw2026.blind-part-publication.v1"}}
    tests = (
        ("absent_receipt", document, unmeasured, "requires an offline native measurement receipt"),
        ("generic_receipt", document, values | {MEASURE: generic}, "requires its exact offline measurement"),
        ("different_epoch", document, stale, "no exact native measurement"),
        ("different_locator", document, wrong_locator, "no exact native measurement"),
        ("new_distance", edited(document, "distance"), values, "no exact native measurement"),
        ("new_angle", edited(document, "angle"), values, "no exact native measurement"),
        ("failed_control", document, values | {MEASURE: unauthorized}, "authenticated offline evidence"),
        ("rehashed_wrong_trial", document, values | {MEASURE: forged}, "authenticated offline evidence"),
        ("occupied_stream", document, values, "empty"),
    )
    for label, model, options, reason in tests:
        for route in ROUTES:
            sink = BytesIO(b"unchanged caller data")
            sink.seek(3 if label != "occupied_stream" else 0)
            position = sink.tell()
            reject(lambda: route(model, sink, options), reason)
            assert sink.getvalue() == b"unchanged caller data" and sink.tell() == position
    return [row[0] for row in tests]


def project(payload, case, branch):
    graph = ReadNativeLink(SldprtArchive.from_bytes(payload), 0, ReadChamfers=True)
    owners = ReadChmfOwn(graph, ColdValue=True)
    assert owners.ModeWord == 1
    design = open_document(BytesIO(payload), source_format=FORMAT, include_brep=False)
    full = open_document(BytesIO(payload), source_format=FORMAT)
    assert full.feature_timeline == design.feature_timeline and full.parameters == design.parameters
    assert design.brep is None
    step, d1, d2, picks = semantic(full, case, branch, owners)
    assert step.definition.angle == d2.value and step.definition.distance == d1.value
    return {"driving_names": [d1.name, d2.name], "typed_slots": [value.DimensionNode.IndexValue for value in owners.DriversValue],
            "persistent_ids": [value.DimensionNode.FieldsValue["f50"] for value in owners.DriversValue],
            "physical": physical(full, case, branch), "bound_selection_paths": [row.path[0].subelement for row in picks]}


def check_paths(document, values, folder, filename, audit):
    target = folder / filename
    sentinel = b"unchanged caller file"
    target.write_bytes(sentinel)
    options = {name: value for name, value in values.items() if name != "final_destination"}
    with audit.active("path"):
        for route in ROUTES:
            reject(lambda: route(document, target, options, overwrite=True), "no exact native measurement")
            diagnostic = "actual final filesystem locator" if route is writer else "no exact native measurement"
            reject(lambda: route(document, target, values, overwrite=True), diagnostic)
    assert set(folder.iterdir()) == {target} and target.read_bytes() == sentinel
    return 2 * len(ROUTES)


def worker(request):
    case, manifest, slot = (request[name] for name in ("case", "manifest", "slot"))
    epoch = EPOCH + slot * 61
    locator = manifest["locator"]
    expected = manifest["archive_sha256"]
    document = authored(case, manifest["branch"][0])
    values = {"final_destination": locator, "require_native_transfers": True, "allow_carrier": False,
              MEASURE: {"written_at": epoch, "receipt": request["receipt"]}}
    phases = tuple(row["receipt_sha256"] for row in request["receipt"]["native_result"]["phases"] if row["slot"] == slot)
    warm_modules()
    with TemporaryDirectory(prefix="KitMeasuredAngle.") as tmp:
        folder, name = Path(tmp), PureWindowsPath(locator).name
        audit = OutputGuard(folder, name)

        def guard(event, args):
            if audit.mode is not None and event.startswith(("socket.", "winreg.")):
                audit.denied_event(event, args)
            audit.audit(event, args)

        sys.addaudithook(guard)
        with audit.active("memory"):
            binary = PrepChmfPart(document, BytesIO(), epoch, WriteOptions(values={"final_destination": locator})).BytesValue
            assert digest(binary) == expected and len(binary) == manifest["writer_proof"]["archive_bytes"]
            streams = typed(binary, case)
            assert streams == manifest["writer_proof"]["stream_sha256"]
            for route in ROUTES:
                sink = BytesIO()
                result = route(document, sink, values)
                assert sink.getvalue() == binary and result.bytes_written == len(binary)
                assert result.vendor_loadable and result.application_usable and not result.dropped
                assert result.native_capabilities == GetDocumentCaps(document) and not result.carrier_capabilities
                evidence = result.metadata[MEASURE]
                assert evidence["generated_sha256"] == expected and evidence["native_result_sha256"] == NATIVE
                assert evidence["generation_sha256"] == TRIAL and evidence["phase_record_sha256"] == phases
            projection = project(binary, case, manifest["branch"])
            negatives = contrasts(document, values)
        path_checks = check_paths(document, values, folder, name, audit) if sys.platform != "win32" else 0
        assert not audit.denied and not any(name.startswith(("pythoncom", "win32com")) for name in sys.modules)
    return {"archive_sha256": expected, "bytes": len(binary), "case": case["name"], "epoch": epoch,
            "routes": [route.__name__ for route in ROUTES], "runtime_accesses": len(audit.denied),
            "unchanged_filesystem_refusals": path_checks, "stream_refusals_on_all_routes": negatives,
            "matched_streams": streams, "linked_replays": 2, "phase_sha256": phases, "projection": projection}


def supervise(trial_path, output):
    trial = locked(trial_path, TRIAL)
    native = locked(RESULT / "ChamferSignedSideNative01.json", NATIVE)
    heldout = locked(RESULT / "EdgeChamferSealedNative03.json", HELDOUT)
    receipt = {"trial": trial, "native_result": native}
    assert native["passed"] and native["proper_distinct_lifetimes"] and native["healthy_controls"]
    assert trial["construction_revision"] == heldout["construction_revision"]
    assert heldout["passed"] and heldout["source_immutability_verified"] and heldout["heldout_lifecycle_credit"] == 2
    rows = []
    for slot, (case, manifest) in enumerate(zip(trial["spec"]["cases"], trial["cases"], strict=True)):
        packet = {"case": case, "manifest": manifest, "slot": slot, "receipt": receipt}
        result = run((sys.executable, "-I", "-B", str(HERE), "--worker"), input=dumps(packet), capture_output=True,
                     text=True, timeout=90, check=False)
        assert result.returncode == 0 and not result.stderr, result.stderr
        rows.append(loads(result.stdout))
    files = ROOT / "src/convert/adapters/solidworks/Core/Writing"
    sources = [*sorted(files.joinpath("Chamfers").glob("*Angle*.py")), files / "Chamfers/EmitChmfMut.py",
               files / "EmitNativeMut.py", HERE]
    report = {"schema": "kit.sw2026.measured-angle-chamfer-sdk.v1", "base": BASE, "python": python_version(),
              "zlib": zlib.ZLIB_RUNTIME_VERSION, "native_result_sha256": NATIVE, "trial_sha256": TRIAL,
              "earlier_heldout_result_sha256": HELDOUT, "new_native_processes": 0, "new_heldout_credit": 0,
              "fresh_guarded_workers": len(rows), "cases": rows,
              "source_sha256": {str(path.relative_to(ROOT)): digest(path.read_bytes()) for path in sources}}
    with output.open("xb") as stream:
        stream.write(canonical(report))
    print(digest(output.read_bytes()))


if __name__ == "__main__":
    if sys.argv[1:] == ["--worker"]:
        print(dumps(worker(loads(sys.stdin.read()))))
    else:
        parser = ArgumentParser()
        parser.add_argument("--trial", type=Path, required=True)
        parser.add_argument("--output", type=Path, required=True)
        args = parser.parse_args()
        supervise(args.trial, args.output)
