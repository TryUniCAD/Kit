from argparse import ArgumentParser
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from io import BytesIO
from pathlib import Path, PureWindowsPath
from subprocess import run
from tempfile import TemporaryDirectory
import json
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(ROOT / "src"), str(HERE.parents[1]), str(HERE.parent)]

from NestedRequest import authored_document, checked
from NestedWriteAudit import Audit, require, snapshot


CASES = {
    "SdkNestedNeutralNative03": "8190fa54206d6a399ae0f5f7eaab79bd1839f13705622b1811801274261dc4ba",
    "SdkRepeatedNeutralNative03": "51bbc71bdf0f675aa63073fbb833b29d4be6f874934a82d5f64f662b2eca1e73",
    "SdkNestedDimensionedNative01": "aed64c337b2410605dea9df94fbdffbd8eb068330895c72bdff71f4f461f1a2c",
    "SdkRepeatedDimensionedNative01": "f869bf0111283bdcac82bf6c4171e6132acda8dfd28c30bb1b8ea166895f3ec0",
}
REFUSALS = {
    "fixed": "AdapterNotFoundError",
    "collision": "FileExistsError",
    "unknown_configuration": "ValueError",
    "symlink": "AdapterNotFoundError",
    "stream": "AdapterNotFoundError",
}
POLICY_REFUSALS = {
    "strict": "ApplicationUsabilityError",
    "missing_native_transfers": "ValueError",
}


def worker(job, area):
    from convert import ApplicationUsabilityError, write_document
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.base.WritePolicy import GetDocumentCaps
    from convert.adapters.solidworks import SldprtAdapter
    from convert.api.ApiContext import GetRegistry

    for encoding in ("ascii", "cp1252", "latin-1", "utf-8", "utf-16-le", "utf-16-be"):
        lookup(encoding)
    request, mode, route = (job[key] for key in ("request", "mode", "route"))
    document, output = authored_document(request)
    if mode == "fixed":
        graph = document.assembly
        document = replace(document, assembly=replace(graph, instances=(replace(graph.instances[0], fixed=True), *graph.instances[1:])))
    document.assert_valid()
    capabilities = GetDocumentCaps(document)
    revision = import_module("convert.adapters.solidworks.Core.Writing.SldprtWriter")
    revision.ReadTime = lambda: output["saved_at"]
    require([type(value).__name__ for value in GetRegistry().writers()
             if value.info.format_id.startswith("solidworks.")] == ["SldprtWriter"], "normal registry changed its writer ownership")
    paths = [PureWindowsPath((row["request"] if row["kind"] == "assembly" else row["request"]["settings"])["output"]["path_name"]).name
             for row in request["definitions"]]
    target = area / PureWindowsPath(output["path_name"]).name
    last = area / next(name for name in reversed(paths) if name != target.name)
    if mode == "collision":
        last.with_name(last.name.lower()).write_bytes(b"independent destination control")
    if mode == "symlink":
        target.symlink_to(area / "unowned" / target.name)
    destination = BytesIO(b"independent caller stream") if mode == "stream" else target
    before = snapshot(area)
    allow_candidate = mode != "strict"
    values = {"native_destination": output["path_name"], "allow_carrier": allow_candidate}
    if mode != "missing_native_transfers":
        values["require_native_transfers"] = True
    configuration = "Unavailable" if mode == "unknown_configuration" else document.configurations[0].id
    audit = Audit(area, target, last, paths, "fresh")
    sys.addaudithook(audit.inspect)
    result, error = None, None
    try:
        if route == "adapter":
            result = SldprtAdapter().write(document, destination, WriteOptions(configuration=configuration, values=values))
        else:
            result = write_document(document, destination, destination_format="solidworks.sldasm",
                                    configuration=configuration, allow_carrier=allow_candidate, values=values)
    except ApplicationUsabilityError as caught:
        require(mode == "strict" and set(caught.issues) == {"application_unusable", "vendor_unloadable"}
                and not caught.carrier_capabilities, "strict publication failed for a reason other than measured attestation")
        error = type(caught).__name__
    except (OSError, ValueError, TypeError, RuntimeError) as caught:
        if mode == "missing_native_transfers":
            require(str(caught) == "unverified SOLIDWORKS assembly candidates require native transfers",
                    "the candidate was refused for a reason other than the missing transfer policy")
        error = type(caught).__name__
    finally:
        audit.active = False
    require(not audit.attempts, "native publication made an external file or runtime access attempt")
    after = snapshot(area)
    if mode != "fresh":
        require(result is None and error == (REFUSALS | POLICY_REFUSALS)[mode] and before == after and not audit.published,
                f"{route} {mode} returned {error}; unchanged output is {before == after}, final attempts {len(audit.published)}")
        if mode == "stream":
            require(destination.getvalue() == b"independent caller stream", "unsupported nested output changed the stream")
        if mode == "strict":
            require(set(audit.staged_write_attempts) == set(paths), "strict attestation did not inspect a complete staged bundle")
        if mode == "missing_native_transfers":
            require(not audit.staged_write_attempts, "a candidate missing native transfer policy wrote files")
        return {"refused": error, "runtime_input_file_reads": 0, "output_unchanged": True,
                "final_publication_attempts": len(audit.published), "staged_files_discarded": len(audit.staged_write_attempts)}
    require(error is None and result is not None and result.path == target and result.adapter == "solidworks.sldasm"
            and result.application_usable is False and result.vendor_loadable is False and not result.dropped
            and not result.requirements and not result.carrier_capabilities and result.native_capabilities == capabilities
            and set(after) == set(audit.published) == set(paths)
            and set(result.metadata["component_file_names"]) == set(paths) - {target.name}
            and result.metadata["bundle_bytes_written"] == sum(row["bytes"] for row in after.values()),
            "nested candidate publication did not report its complete native transfer and unmeasured owned bundle")
    return {"files": after, "runtime_input_file_reads": 0, "native_transfers": sorted(str(value) for value in result.native_capabilities),
            "application_usable": result.application_usable, "vendor_loadable": result.vendor_loadable,
            "candidate_profile": result.metadata["candidate_profile"]}


def run_worker(request, route, mode):
    with TemporaryDirectory(prefix="KitPublicNestedPublication.") as folder:
        command = (sys.executable, "-I", "-B", str(HERE), "--worker", str(Path(folder).resolve()))
        process = run(command, input=json.dumps({"request": request, "route": route, "mode": mode}), capture_output=True, text=True, timeout=180)
    require(process.returncode == 0 and not process.stderr, process.stderr[-2500:])
    return json.loads(process.stdout)


def measure(workspace):
    rows = {}
    api_routes = ("registry", "adapter")
    for name, pin in CASES.items():
        folder = workspace / name
        packet = json.loads(checked(folder / "Packet.json", pin))
        fixture = json.loads(checked(folder / "Fixture.json", packet["fixture_sha256"]))
        request = json.loads(checked(folder / "NeutralRequest.json", fixture["request_sha256"]))
        expected = {row["file"]: {"bytes": row["bytes"], "sha256": row["sha256"]} for row in fixture["files"].values()}
        routes = {route: run_worker(request, route, "fresh") for route in api_routes}
        require(routes["registry"] == routes["adapter"] and routes["registry"]["files"] == expected,
                "public nested output changed the native-verified document bytes")
        rows[name] = {"packet_sha256": pin, **routes["registry"]}
    refusals = {mode: run_worker(request, "adapter", mode) for mode in REFUSALS}
    policy = {route: {mode: run_worker(request, route, mode) for mode in POLICY_REFUSALS} for route in api_routes}
    return {"schema": "kit.sw2026.public-nested-candidates.v1", "cases": rows, "refusals": refusals, "policy_refusals": policy,
            "guarded_processes": len(api_routes) * (len(rows) + len(POLICY_REFUSALS)) + len(refusals),
            "native_processes_started": 0, "heldout_inputs_read": 0}


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--worker", type=Path)
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(worker(json.load(sys.stdin), args.worker), sort_keys=True, allow_nan=False))
    else:
        raw = (json.dumps(measure(args.workspace), sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
        with args.output.open("xb") as output:
            output.write(raw)
        print(sha256(raw).hexdigest())
