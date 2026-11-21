from argparse import ArgumentParser
from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
from subprocess import check_output, run
import sys
from tarfile import open as open_tar
from tempfile import TemporaryDirectory
from time import time

HERE = Path(__file__).resolve()
ORIGINAL = "b0cf2bd0b664b7f1c6a3d039ba520360f47c1ab15a5a15b5f629b775aacf71ea"
NATIVE = "48de61872b805bcb2acf3cec9f8d6a491629e3b1a9560f452985c2583b0658de"
OLD_WRITER = "e8b7a00dc166443cb575328b5210c4bf8593b782"
PUBLIC_WRITER = "96fe5d97f67efc03bcf394f9b3e3caaa5e9469fb"
PUBLIC_TREE = "4f00d8b078ea956ccfa2883c043093a964ae2237"
PUBLIC_RESULT = "re/solidworks/measurements/2026/SdkPublicNestedWriting01.json"
PUBLIC_RESULT_SHA = "2cb15c011cad7cd489a3657c65765192cfb9bd7a08d2c46128375d892f1df41a"
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
SCHEMA = "kit.sw2026.sealed-public-nested-parity.v1"
CODE_SCHEMA = "kit.sw2026.sealed-public-nested-code.v1"
WORKER = "re/tooling/sw2026/nested_publication/MeasurePublicNestedWriting.py"
HELPERS = (
    WORKER,
    "re/tooling/sw2026/nested_publication/MeasureNestedPublication.py",
    "re/tooling/sw2026/AuditNestedNeutralComposition.py",
    "re/tooling/sw2026/SdkNativeRoundTrips.py",
)
PHASES = ("before", "build", "generated", "reopen", "after", "qualify")
NATIVE_PHASES = ("before", "generated", "reopen", "after")
ROUTES = ("registry", "adapter")
ORIGINAL_CHECK = "RunSealedNestedEvaluation.py"
LOCAL_LOADER = "import runpy,sys; sys.path.insert(0,sys.argv[1]); sys.argv=sys.argv[2:]; runpy.run_path(sys.argv[0],run_name='__main__')"
DISCLOSED = {
    "SdkNestedNeutralNative03": "8190fa54206d6a399ae0f5f7eaab79bd1839f13705622b1811801274261dc4ba",
    "SdkRepeatedNeutralNative03": "51bbc71bdf0f675aa63073fbb833b29d4be6f874934a82d5f64f662b2eca1e73",
}
PUBLIC_CASES = {
    **DISCLOSED,
    "SdkNestedDimensionedNative01": "aed64c337b2410605dea9df94fbdffbd8eb068330895c72bdff71f4f461f1a2c",
    "SdkRepeatedDimensionedNative01": "f869bf0111283bdcac82bf6c4171e6132acda8dfd28c30bb1b8ea166895f3ec0",
}
NATIVE_TRANSFERS = ["assemblies", "body_structure", "component_documents", "configurations", "editable_sketches",
                    "parameters", "parametric_history", "support_planes"]


class ParityFailure(ValueError):
    pass


def require(condition, diagnostic):
    if not condition:
        raise ParityFailure(diagnostic)


def is_pin(value, size=64):
    return isinstance(value, str) and re.fullmatch(f"[0-9a-f]{{{size}}}", value) is not None


def hash_bytes(raw):
    return sha256(raw).hexdigest()


def value_hash(value):
    return hash_bytes(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode())


def checked(path, expected, owner):
    require(is_pin(expected) and path.is_relative_to(owner) and path.resolve(strict=True) == path
            and path.is_file() and not path.is_symlink(), "input is not a pinned regular file under its owner")
    raw = path.read_bytes()
    require(hash_bytes(raw) == expected, "frozen artifact differs from its pinned identity")
    return raw


def read(path, expected, owner):
    return json.loads(checked(path, expected, owner))


def write(path, raw):
    with path.open("xb") as file:
        file.write(raw)
    return hash_bytes(raw)


def write_json(path, value):
    return write(path, (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode())


def public_phases(root, row):
    slot = row["slot"]
    require(row["qualified"] is True and tuple(item["phase"] for item in row["phases"]) == PHASES,
            "prior public qualification is incomplete")
    base = root / "Progress" / f"Slot{slot:02d}" / "T01"
    phases = {}
    for proof in row["phases"]:
        phase = proof["phase"]
        require(proof["attempt"] == 1 and proof["passed"] is True, "prior sealed phase did not pass")
        record = read(base / phase / "1" / "Record.json", proof["public_record_sha256"], root)
        require(record["packet_sha256"] == ORIGINAL and record["trial"] == "T01"
                and record["slot"] == slot and record["phase"] == phase and record["stage"] == "passed"
                and all(record[key] == proof[key] for key in ("attempt", "passed", "started_at", "finished_at", "private_record_sha256"))
                and record["started_at"] <= record["finished_at"], "prior phase identity differs from the native result")
        if phase in NATIVE_PHASES:
            identity = record["identity"]
            require(identity == proof["identity"] and identity["file_version"] == "34.5.2.0604"
                    and identity["sha256"] == ORACLE and type(identity["process_creation_filetime"]) is int
                    and identity["process_creation_filetime"] > 0, "prior native phase has the wrong application identity")
        phases[phase] = record
    require(all(first["finished_at"] <= second["started_at"] for first, second in zip(phases.values(), tuple(phases.values())[1:]))
            and phases["qualify"]["qualified"] is True, "prior native phases lack their original healthy brackets")
    build = phases["build"]
    require(all(is_pin(build[key]) for key in ("build_lock_sha256", "code_lock_sha256", "request_sha256", "prediction_sha256"))
            and is_pin(row["generated_artifact_manifest_sha256"]) and is_pin(row["saved_artifact_manifest_sha256"])
            and build["generated_artifact_manifest_sha256"] == phases["qualify"]["generated_artifact_manifest_sha256"]
            == row["generated_artifact_manifest_sha256"]
            and all(phases[phase]["saved_artifact_manifest_sha256"] == row["saved_artifact_manifest_sha256"]
                    for phase in ("generated", "reopen", "qualify")), "prior build or saved manifest cannot be attributed")
    return phases


def original_capsule(root):
    root = root.resolve(strict=True)
    packet = read(root / "Evaluation.json", ORIGINAL, root)
    result = read(root / "Progress" / "EvaluationResults.json", NATIVE, root)
    require(packet["schema"] == "kit.sw2026.sealed-nested-writer-evaluation.v1"
            and packet["writer_profile"] == "neutral_dimensioned_rectangle" and packet["oracle_sha256"] == ORACLE
            and result["schema"] == "kit.sw2026.sealed-nested-writer-public-result.v1"
            and result["packet_sha256"] == ORIGINAL and packet["writer_revision"] == result["writer_revision"] == OLD_WRITER
            and all(packet[key] == result[key] for key in ("code_manifest_sha256", "source_lock_sha256", "tools_sha256"))
            and result["heldout_profiles_native_passed"] is True and result["controls_healthy"] is True
            and result["distinct_native_processes"] == 8 and result["source_before_execution_verified_by_frozen_guest"] is True
            and result["host_heldout_payloads_read"] == 0 and result["heldout_results_remain_sealed"] is True
            and result["public_adapter_writer_qualified"] is False, "original capsule does not contain both prior native passes")
    tools = root / "Tools"
    require(ORIGINAL_CHECK in packet["tools_sha256"] and
            {path.name for path in tools.iterdir()} == set(packet["tools_sha256"]), "original sealed verifier closure differs")
    for name, pin in packet["tools_sha256"].items():
        checked(tools / name, pin, tools)
    command = (sys.executable, "-I", "-B", "-c", LOCAL_LOADER, str(tools), str(tools / ORIGINAL_CHECK),
               "verify", str(root / "Evaluation.json"), "--packet-sha256", ORIGINAL)
    verification = run(command, capture_output=True, timeout=180)
    require(verification.returncode == 0 and not verification.stderr
            and json.loads(verification.stdout) == {"verified_packet": ORIGINAL, "host_heldout_payloads_read": 0},
            "the prior frozen verifier refused the original capsule")
    require(tuple(row["slot"] for row in result["slots"]) == (1, 2), "expected both opaque sealed slots")
    by_slot = {row["slot"]: public_phases(root, row) for row in result["slots"]}
    native = [phases[item] for phases in by_slot.values() for item in NATIVE_PHASES]
    require(len({row["identity"]["process_creation_filetime"] for row in native}) == 8
            and all(first["finished_at"] <= second["started_at"] for first, second in zip(native, native[1:])),
            "prior native processes were reused or overlapped")
    return packet, by_slot


def code_entry(name):
    path = PurePosixPath(name)
    require(path.as_posix() == name and not path.is_absolute() and path.suffix == ".py"
            and all(re.fullmatch(r"[A-Za-z0-9_.-]+", part) and part not in (".", "..") for part in path.parts)
            and (path.parts[0] == "src" or name in HELPERS), "writer code cannot contain captured fixtures or escaped paths")
    return path


def git(checkout, *arguments):
    return check_output(("git", "-C", str(checkout), *arguments))


def verify_public_routes(record):
    require(record["schema"] == "kit.sw2026.public-nested-writing.v1"
            and record["guarded_processes"] == 13 and record["native_processes_started"] == record["heldout_inputs_read"] == 0
            and set(record["cases"]) == set(PUBLIC_CASES) and len(record["refusals"]) == 5,
            "committed public route proof has the wrong scope")
    for name, row in record["cases"].items():
        require(row["packet_sha256"] == PUBLIC_CASES[name]
                and row["application_usable"] is True and row["vendor_loadable"] is True
                and row["runtime_input_file_reads"] == 0 and row["native_transfers"] == NATIVE_TRANSFERS
                and row["qualification"] == "2026_rigid_nested_assembly",
                "committed public route proof lacks positive native transfer")


def freeze(args):
    require(HERE.parent.name == "nested_publication", "freeze from the committed repository tool")
    checkout = HERE.parents[4]
    evaluation, _ = original_capsule(args.original)
    revision, runner = args.sdk_revision, git(checkout, "rev-parse", "HEAD").decode().strip()
    require(revision == PUBLIC_WRITER and git(checkout, "rev-parse", "--verify", revision + "^{commit}").decode().strip() == revision
            and git(checkout, "merge-base", OLD_WRITER, revision).decode().strip() == OLD_WRITER,
            "public writer snapshot needs its exact committed descendant revision")
    sdk_tree = git(checkout, "rev-parse", revision + ":src").decode().strip()
    public_proof = git(checkout, "show", f"{revision}:{PUBLIC_RESULT}")
    require(sdk_tree == PUBLIC_TREE and hash_bytes(public_proof) == PUBLIC_RESULT_SHA,
            "committed public writer closure or disclosed proof differs")
    verify_public_routes(json.loads(public_proof))
    tool_data = git(checkout, "show", f"{runner}:{HERE.relative_to(checkout).as_posix()}")
    require(tool_data == HERE.read_bytes(), "the parity evaluator must be committed before freezing")
    output = args.output.absolute()
    require(output.parent.resolve(strict=True) == output.parent and not output.exists() and not output.is_symlink()
            and not output.is_relative_to(checkout) and not output.is_relative_to(args.original.resolve()),
            "choose an unused packet destination outside both original data and repository")
    raw = git(checkout, "archive", revision, "--", "src", *HELPERS)
    output.mkdir()
    write(output / "DisclosedPublicRoutes.json", public_proof)
    code = output / "CodeRoot"
    code.mkdir()
    manifest = {}
    with open_tar(fileobj=BytesIO(raw)) as files:
        for entry in files:
            if not entry.name.endswith(".py"):
                continue
            relative = code_entry(entry.name)
            require(entry.isfile(), "snapshot contains nonregular Python source")
            destination = code / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            with files.extractfile(entry) as source:
                manifest[relative.as_posix()] = write(destination, source.read())
    require(set(HELPERS) <= set(manifest) and "src/convert/__init__.py" in manifest, "writer snapshot is incomplete")
    code_pin = write_json(output / "CodeManifest.json", {"schema": CODE_SCHEMA, "writer_revision": revision,
                                                        "sdk_tree": sdk_tree, "files_sha256": manifest})
    tools = output / "Tools"
    tools.mkdir()
    tool_pin = write(tools / HERE.name, tool_data)
    pin = write_json(output / "Parity.json", {"schema": SCHEMA, "original_packet_sha256": ORIGINAL,
                     "original_native_result_sha256": NATIVE, "original_source_lock_sha256": evaluation["source_lock_sha256"],
                     "disclosed_public_routes_sha256": PUBLIC_RESULT_SHA,
                     "sdk_revision": revision, "sdk_tree": sdk_tree, "code_manifest_sha256": code_pin,
                     "evaluator_revision": runner, "evaluator_sha256": tool_pin})
    code_snapshot(output / "Parity.json", pin, executed_tool=False)
    return {"passed": True, "parity_packet_sha256": pin, "source_manifest_sha256": code_pin,
            "sdk_revision": revision, "sdk_tree": sdk_tree, "public_native_slots_verified": 2, "private_requests_read": 0}


def code_snapshot(path, pin, executed_tool=True):
    path = path.absolute()
    root = path.parent
    require(path.name == "Parity.json" and root.resolve(strict=True) == root, "expected the exact frozen packet path")
    packet = read(path, pin, root)
    require(set(packet) == {"schema", "original_packet_sha256", "original_native_result_sha256", "original_source_lock_sha256",
                            "disclosed_public_routes_sha256", "sdk_revision", "sdk_tree", "code_manifest_sha256",
                            "evaluator_revision", "evaluator_sha256"}
            and packet["schema"] == SCHEMA and packet["original_packet_sha256"] == ORIGINAL
            and packet["original_native_result_sha256"] == NATIVE and packet["sdk_revision"] == PUBLIC_WRITER
            and packet["sdk_tree"] == PUBLIC_TREE and packet["disclosed_public_routes_sha256"] == PUBLIC_RESULT_SHA
            and all(is_pin(packet[key], 40) for key in ("sdk_revision", "sdk_tree", "evaluator_revision")),
            "unexpected current writer snapshot identity")
    verify_public_routes(read(root / "DisclosedPublicRoutes.json", PUBLIC_RESULT_SHA, root))
    tool = root / "Tools" / HERE.name
    require(not executed_tool or HERE == tool, "execute the evaluator frozen inside this packet")
    checked(tool, packet["evaluator_sha256"], root)
    manifest = read(root / "CodeManifest.json", packet["code_manifest_sha256"], root)
    code = root / "CodeRoot"
    require(manifest["schema"] == CODE_SCHEMA and manifest["writer_revision"] == packet["sdk_revision"]
            and manifest["sdk_tree"] == packet["sdk_tree"]
            and set(HELPERS) <= set(manifest["files_sha256"]), "code manifest differs from the frozen writer")
    require({item.relative_to(code).as_posix() for item in code.rglob("*") if not item.is_dir()} == set(manifest["files_sha256"]),
            "frozen code closure contains a missing or extra file")
    for name, wanted in manifest["files_sha256"].items():
        checked(code / code_entry(name), wanted, code)
    return root, packet, code


def fixed_directory(value):
    import ctypes

    private = Path(value)
    drive_type = ctypes.windll.kernel32.GetDriveTypeW
    drive_type.argtypes, drive_type.restype = (ctypes.c_wchar_p,), ctypes.c_uint
    require(re.fullmatch(r"[A-Za-z]:", private.drive) and private.resolve(strict=True) == private
            and private.is_dir() and drive_type(private.anchor) == 3,
            "private parity requires a canonical fixed guest-local base")
    return private


def qualified_request(private, phases, old):
    build, qualification = phases["build"], phases["qualify"]
    lock = read(private / "BuildLock.json", build["build_lock_sha256"], private)
    require(lock["packet_sha256"] == ORIGINAL and lock["writer_revision"] == OLD_WRITER
            and lock["runtime_file_read_attempts"] == 0 and lock["two_process_byte_identity"] is True
            and lock["source_before_execution_verified"] is True
            and all(lock[key] == build[key] for key in ("code_lock_sha256", "request_sha256", "prediction_sha256",
                                                        "generated_artifact_manifest_sha256")),
            "guest BuildLock does not belong to the native-tested generation")
    prior_code = read(private / "CodeLocked.json", lock["code_lock_sha256"], private)
    prior_request = read(private / "RequestLock.json", lock["request_lock_sha256"], private)
    require(prior_code["packet_sha256"] == prior_request["packet_sha256"] == ORIGINAL and prior_code["writer_revision"] == OLD_WRITER
            and prior_code["code_manifest_sha256"] == old["code_manifest_sha256"] and prior_code["tools_sha256"] == old["tools_sha256"]
            and prior_code["source_lock_sha256"] == old["source_lock_sha256"]
            and prior_request["code_lock_sha256"] == lock["code_lock_sha256"]
            and prior_request["request_sha256"] == lock["request_sha256"] and prior_request["prediction_sha256"] == lock["prediction_sha256"]
            and prior_code["locked_at"] <= prior_request["source_exposed_at"] <= prior_request["locked_at"] <= lock["build_started_at"]
            <= lock["build_finished_at"] <= phases["generated"]["started_at"],
            "the original source exposure and immutable build chronology disagree")
    expected = {}
    for row in lock["files"].values():
        name = row["file"]
        require(PureWindowsPath(name).name == name and name
                and PureWindowsPath(name).suffix in (".SLDASM", ".SLDPRT")
                and name.casefold() not in {value.casefold() for value in expected}
                and is_pin(row["sha256"]) and type(row["bytes"]) is int and row["bytes"] > 0,
                "prior BuildLock lists an invalid output")
        expected[name] = {"sha256": row["sha256"], "bytes": row["bytes"]}
    require(len(expected) >= 3 and value_hash(expected) == lock["generated_artifact_manifest_sha256"]
            == qualification["generated_artifact_manifest_sha256"], "complete BuildLock inventory differs from the native-pass manifest")
    request = read(private / "Request.json", lock["request_sha256"], private)
    bindings = {}
    epochs = set()
    for row in request["definitions"]:
        body = row["request"]
        require(row["kind"] in ("part", "assembly") and row["id"] not in bindings, "invalid locked neutral definition")
        output = (body if row["kind"] == "assembly" else body["settings"])["output"]
        locator = PureWindowsPath(output["path_name"])
        require(locator.is_absolute() and locator.parent == PureWindowsPath(private / "GeneratedInput")
                and locator.name == lock["files"][row["id"]]["file"]
                and locator.suffix == (".SLDASM" if row["kind"] == "assembly" else ".SLDPRT")
                and type(output["saved_at"]) is int and output["saved_at"] > 0, "locked request locator or clock differs")
        bindings[row["id"]] = locator.name
        epochs.add(output["saved_at"])
    require(len(epochs) == 1 and set(bindings) == set(lock["files"]) and bindings[request["root"]].endswith(".SLDASM"),
            "locked neutral request does not own the complete single-clock bundle")
    return request, expected


def compare_worker(code, private, route, request, expected):
    with TemporaryDirectory(prefix=route + ".", dir=private) as folder:
        command = (sys.executable, "-I", "-B", str(code / WORKER), "--worker", str(Path(folder).resolve()))
        job = {"request": request, "route": route, "mode": "fresh"}
        process = run(command, input=json.dumps(job, allow_nan=False).encode(), capture_output=True, timeout=180, cwd=code)
        require(process.returncode == 0 and not process.stderr, "frozen public writer worker failed")
        report = json.loads(process.stdout)
        require(set(report) == {"files", "runtime_input_file_reads", "native_transfers", "application_usable",
                                "vendor_loadable", "qualification"}
                and report["runtime_input_file_reads"] == 0 and report["application_usable"] is True
                and report["vendor_loadable"] is True and report["qualification"] == "2026_rigid_nested_assembly"
                and report["native_transfers"] == NATIVE_TRANSFERS, "public writer lost qualification or native transfer")
        require(report["files"] == expected, "public writer differs from a native-tested bundle file")
        return {"files_compared": len(expected), "generated_artifact_manifest_sha256": value_hash(report["files"]),
                "native_transfer_count": len(report["native_transfers"]), "runtime_input_file_reads": 0,
                "vendor_loadable": True, "application_usable": True, "byte_identity": True}


def disclosed_preflight(code, workspace):
    output = {}
    for case, pin in DISCLOSED.items():
        folder = (workspace / case).resolve(strict=True)
        packet = read(folder / "Packet.json", pin, folder)
        fixture = read(folder / "Fixture.json", packet["fixture_sha256"], folder)
        request = read(folder / "NeutralRequest.json", fixture["request_sha256"], folder)
        expected = {row["file"]: {"sha256": row["sha256"], "bytes": row["bytes"]} for row in fixture["files"].values()}
        with TemporaryDirectory(prefix="KitPublicNestedPreflight.") as work:
            rows = [compare_worker(code, work, route, request, expected) for route in ROUTES]
        require(rows[0] == rows[1], "disclosed public routes produced different qualification evidence")
        output[case] = rows[0]
    return output


def verify_command(args):
    _, packet, code = code_snapshot(args.packet, args.packet_sha256)
    old, _ = original_capsule(args.original)
    require(packet["original_source_lock_sha256"] == old["source_lock_sha256"], "source lock pin differs")
    record = {"passed": True, "parity_packet_sha256": args.packet_sha256, "sdk_revision": packet["sdk_revision"],
              "public_native_slots_verified": 2, "private_requests_read": 0, "native_processes_started": 0}
    if args.disclosed_workspace:
        record["disclosed_preflight"] = disclosed_preflight(code, args.disclosed_workspace)
    return record


def run_guest(args, context):
    context["stage"] = "guest_only"
    require(os.name == "nt", "sealed neutral requests may only be accessed in the Windows guest")
    context["stage"] = "verify_public_evidence"
    root, packet, code = code_snapshot(args.packet, args.packet_sha256)
    old, slots = original_capsule(args.original)
    require(packet["original_source_lock_sha256"] == old["source_lock_sha256"], "source lock pin differs")
    result = root / "Result.json"
    require(not result.exists() and not result.is_symlink(), "choose a fresh parity packet")
    context["output"] = result
    context["stage"] = "lock_current_code"
    base = fixed_directory(old["guest_private_base"])
    private = base / "PublicParity" / args.packet_sha256
    require(private.resolve() == private, "current parity scratch escaped its fixed-drive owner")
    private.mkdir(parents=True, exist_ok=False)
    code_lock = private / "CodeLocked.json"
    frozen = {"parity_packet_sha256": args.packet_sha256, "sdk_revision": packet["sdk_revision"],
              "code_manifest_sha256": packet["code_manifest_sha256"], "original_native_result_sha256": NATIVE, "locked_at": time()}
    code_pin = write_json(code_lock, frozen)
    rows = []
    for slot, phases in slots.items():
        context.update({"stage": "verify_locked_request", "slot": slot})
        source = base / ORIGINAL / f"Slot{slot:02d}" / "T01"
        require(source.resolve(strict=True) == source and source.is_dir() and read(code_lock, code_pin, private) == frozen
                and frozen["locked_at"] <= time(), "fresh code lock or prior sealed trial differs")
        request, expected = qualified_request(source, phases, old)
        routes = {}
        for route in ROUTES:
            context.update({"stage": "compare_public_route", "route": route})
            routes[route] = compare_worker(code, private, route, request, expected)
        require(routes["registry"] == routes["adapter"], "public routes produced different parity evidence")
        context.pop("route")
        rows.append({"slot": slot, "request_sha256": phases["build"]["request_sha256"],
                     "build_lock_sha256": phases["build"]["build_lock_sha256"], "routes": routes})
    context.update({"stage": "recheck_frozen_evidence"})
    code_snapshot(args.packet, args.packet_sha256)
    _, final_slots = original_capsule(args.original)
    require(final_slots == slots and read(code_lock, code_pin, private) == frozen, "frozen parity authorities changed during execution")
    for slot, phases in slots.items():
        source = base / ORIGINAL / f"Slot{slot:02d}" / "T01"
        checked(source / "BuildLock.json", phases["build"]["build_lock_sha256"], source)
        checked(source / "Request.json", phases["build"]["request_sha256"], source)
    record = {"schema": SCHEMA, "passed": True, "parity_packet_sha256": args.packet_sha256,
              "original_packet_sha256": ORIGINAL, "original_native_result_sha256": NATIVE,
              "disclosed_public_routes_sha256": PUBLIC_RESULT_SHA,
              "sdk_revision": packet["sdk_revision"], "sdk_tree": packet["sdk_tree"],
              "code_manifest_sha256": packet["code_manifest_sha256"], "code_lock_sha256": code_pin,
              "public_route_byte_identity": True, "prior_native_acceptance_linked_by_exact_byte_identity": True,
              "files_compared_per_route": sum(row["routes"]["registry"]["files_compared"] for row in rows),
              "fresh_guarded_sdk_processes": 4, "native_processes_started": 0,
              "host_private_requests_read": 0, "sealed_requests_verified_on_guest": 2,
              "native_or_saved_artifact_files_read": 0, "slots": rows}
    write_json(result, record)
    return record


def main():
    parser = ArgumentParser()
    modes = parser.add_subparsers(dest="action", required=True)
    freeze_mode = modes.add_parser("freeze")
    freeze_mode.add_argument("--sdk-revision", required=True)
    freeze_mode.add_argument("--original", type=Path, required=True)
    freeze_mode.add_argument("--output", type=Path, required=True)
    for mode in ("verify", "run"):
        command = modes.add_parser(mode)
        command.add_argument("packet", type=Path)
        command.add_argument("--packet-sha256", required=True)
        command.add_argument("--original", type=Path, required=True)
        if mode == "verify":
            command.add_argument("--disclosed-workspace", type=Path)
    args = parser.parse_args()
    context = {"stage": args.action}
    try:
        if args.action == "freeze":
            result = freeze(args)
        elif args.action == "verify":
            result = verify_command(args)
        else:
            result = run_guest(args, context)
    except Exception as error:
        if args.action != "run":
            raise
        output = context.pop("output", None)
        result = {"schema": SCHEMA, "passed": False, "parity_packet_sha256": args.packet_sha256,
                  "native_processes_started": 0, "error_type": type(error).__name__, **context}
        if type(error) is ParityFailure:
            result["predicate"] = str(error)
        if output is not None:
            write_json(output, result)
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return int(not result["passed"])


if __name__ == "__main__":
    raise SystemExit(main())
