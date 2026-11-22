from argparse import ArgumentParser
from codecs import lookup
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path, PureWindowsPath
from subprocess import run
import sys
from tempfile import TemporaryDirectory

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(ROOT / "src"), str(HERE.parent)]

from NestedRequest import authored_document
from NestedWriteAudit import Audit, require, snapshot
from ReadNestedEvidence import TERMINALS, measured_request
from ProveNestedDelivery import REFUSALS

EVIDENCE_REFUSALS = {
    "missing_receipt": "requires an offline native measurement receipt",
    "bad_control": "requires the matching passing SOLIDWORKS 2026 SP05.2 report",
    "bad_phase": "has an unclean or unidentified phase",
    "duplicate_process": "repeats or overlaps an oracle lifetime",
    "epoch_drift": "requires the matching passing SOLIDWORKS 2026 SP05.2 report",
    "unmeasured_epoch": "does not match the exact member",
    "changed_pose": "does not match the exact member",
    "wrong_child_digest": "does not match the exact member",
    "wrong_child_size": "does not match the exact member",
    "wrong_child_name": "does not match the exact member",
    "wrong_child_configuration": "does not match the exact member",
    "wrong_child_order": "does not match the exact member",
    "reordered_members": "does not match the exact member",
    "missing_member": "has a different root namespace or member closure",
    "wrong_namespace": "has a different root namespace or member closure",
}


def adjusted_measurement(envelope, mode):
    envelope = deepcopy(envelope)
    receipt = envelope["receipt"]
    row = receipt["members"][0]
    if mode == "missing_receipt":
        return {}
    if mode == "bad_control":
        receipt["controls_healthy"] = False
    elif mode == "bad_phase":
        receipt["phases"][-1]["open_warnings"] = 1
    elif mode == "duplicate_process":
        phase, peer = receipt["phases"][:2]
        for key in ("process_id", "process_creation_filetime"):
            peer[key] = phase[key]
    elif mode == "epoch_drift":
        envelope["written_at"] += 1
    elif mode == "unmeasured_epoch":
        envelope["written_at"] += 1
        receipt["written_at"] += 1
    elif mode == "wrong_child_digest":
        row["sha256"] = receipt["members"][-1]["sha256"]
    elif mode == "wrong_child_size":
        row["bytes"] += 1
    elif mode == "wrong_child_name":
        row["name"] = row["name"].lower()
    elif mode == "wrong_child_configuration":
        row["configuration"] = "Default"
    elif mode == "wrong_child_order":
        receipt["members"][-1]["children"].reverse()
    elif mode == "reordered_members":
        receipt["members"][:2] = reversed(receipt["members"][:2])
    elif mode == "missing_member":
        receipt["members"].pop(0)
    elif mode == "wrong_namespace":
        receipt["namespace"] += "\\Unmeasured"
    return {"solidworks_native_measurement": envelope}


def worker(job, area):
    from convert import write_document
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.base.WritePolicy import GetDocumentCaps
    from convert.adapters.solidworks import SldprtAdapter

    for encoding in ("ascii", "cp1252", "latin-1", "utf-8", "utf-16-le", "utf-16-be"):
        lookup(encoding)
    request, envelope, route, mode = (job[key] for key in ("request", "envelope", "route", "mode"))
    if mode == "changed_pose":
        root, = (row for row in request["definitions"] if row["id"] == request["root"])
        root["occurrences"][0]["occurrence"]["origin"][0] += 0.001
    document, output = authored_document(request)
    if mode == "fixed":
        graph = document.assembly
        document = replace(document, assembly=replace(graph, instances=(replace(graph.instances[0], fixed=True), *graph.instances[1:])))
    document.assert_valid()
    capabilities = GetDocumentCaps(document)
    receipt = envelope["receipt"]
    expected = {row["name"]: {key: row[key] for key in ("bytes", "sha256")} for row in receipt["members"]}
    target = area / PureWindowsPath(output["path_name"]).name
    last = area / receipt["members"][-2]["name"]
    if mode == "collision":
        last.with_name(last.name.lower()).write_bytes(b"independent sibling control")
    if mode == "symlink":
        target.symlink_to(area / "unowned" / target.name)
    destination = BytesIO(b"independent caller stream") if mode == "stream" else target
    before = snapshot(area)
    options = {"native_destination": output["path_name"], "allow_carrier": False, "require_native_transfers": True,
               **adjusted_measurement(envelope, mode)}
    configuration = "Unavailable" if mode == "unknown_configuration" else document.configurations[0].id
    audit = Audit(area, target, last, expected, mode)
    sys.addaudithook(audit.inspect)
    result, error = None, None
    try:
        if route == "adapter":
            result = SldprtAdapter().write(document, destination, WriteOptions(configuration=configuration, values=options))
        else:
            result = write_document(document, destination, destination_format="solidworks.sldasm", configuration=configuration,
                                    allow_carrier=False, values=options)
    except (OSError, ValueError, TypeError, RuntimeError) as caught:
        error = caught
    finally:
        audit.active = False
    require(not audit.attempts, "assembly publication attempted external input or runtime access")
    after = snapshot(area)
    if mode != "measured":
        require(result is None and error is not None and before == after, f"{route} {mode} changed the caller's destination")
        if mode == "publish-denied":
            require(type(error) is PermissionError and audit.published == [target.name, last.name]
                    and set(audit.staged_write_attempts) == set(expected), "verified bundle did not roll back the controlled publication failure")
        else:
            require(not audit.published and not audit.staged_write_attempts, "assembly refusal began writing staged files")
            if mode in EVIDENCE_REFUSALS:
                require(type(error) is ValueError and EVIDENCE_REFUSALS[mode] in str(error), f"{route} {mode} refused for {error}")
            else:
                require(type(error).__name__ == REFUSALS[mode], f"{mode} refused for {error}")
        if mode == "stream":
            require(destination.getvalue() == b"independent caller stream", "unsupported assembly destination changed the caller stream")
        return {"refused": type(error).__name__, "destination_unchanged": True, "staged_attempts": len(audit.staged_write_attempts),
                "final_attempts": len(audit.published), "runtime_input_reads": 0}
    require(error is None and result is not None and result.path == target and result.adapter == "solidworks.sldasm"
            and result.application_usable is True and result.vendor_loadable is True
            and result.native_capabilities == capabilities and not result.carrier_capabilities and not result.requirements and not result.dropped
            and after == expected and set(audit.published) == set(expected),
            f"{route} could not verify and publish the complete measured bundle: {error}")
    require(dict(result.metadata["solidworks_native_measurement"]) == {
        key: receipt[key] for key in ("native_result_sha256", "packet_sha256", "fixture_sha256")
    }, "published measurement metadata does not identify its exact bundle")
    return {"files": after, "native_transfers": sorted(str(value) for value in result.native_capabilities),
            "oracle_terminal_sha256": receipt["native_result_sha256"], "written_at": envelope["written_at"],
            "application_usable": result.application_usable, "vendor_loadable": result.vendor_loadable, "runtime_input_reads": 0}


def run_worker(request, envelope, route, mode):
    with TemporaryDirectory(prefix="KitMeasuredNested.") as folder:
        completed = run((sys.executable, "-I", "-B", str(HERE), "--worker", str(Path(folder).resolve())),
                        input=json.dumps({"request": request, "envelope": envelope, "route": route, "mode": mode}),
                        text=True, capture_output=True, timeout=180)
    require(completed.returncode == 0 and not completed.stderr, completed.stderr[-2600:])
    return json.loads(completed.stdout)


def measure(workspace):
    result = {}
    routes = ("registry", "adapter")
    for case in TERMINALS:
        request, envelope = measured_request(workspace, case)
        observed = [run_worker(request, envelope, route, "measured") for route in routes]
        require(observed[0] == observed[1], "direct and registry evidence publication differ")
        result[case] = observed[0]
    refusals = {mode: run_worker(request, envelope, "adapter", mode) for mode in REFUSALS}
    for mode in EVIDENCE_REFUSALS:
        observed = [run_worker(request, envelope, route, mode) for route in routes]
        require(observed[0] == observed[1], f"{mode} behaves differently between public routes")
        refusals[mode] = observed[0]
    rollback = run_worker(request, envelope, "registry", "publish-denied")
    return {"schema": "kit.sw2026.measured-nested-publication-proof.v1", "cases": result, "refusals": refusals,
            "verified_publication_rollback": rollback, "native_processes_started": 0, "protected_inputs_read": 0,
            "guarded_processes": 2 * (len(result) + len(EVIDENCE_REFUSALS)) + len(REFUSALS) + 1}


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--worker", type=Path)
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--receipt-case", choices=tuple(TERMINALS))
    args = parser.parse_args()
    if args.worker is not None:
        print(json.dumps(worker(json.load(sys.stdin), args.worker), sort_keys=True, allow_nan=False))
    elif args.workspace is None or args.output is None:
        parser.error("a disclosed workspace and new output are required")
    else:
        result = measured_request(args.workspace, args.receipt_case)[1] if args.receipt_case else measure(args.workspace)
        raw = (json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
        with args.output.open("xb") as output:
            output.write(raw)
        print(sha256(raw).hexdigest())
