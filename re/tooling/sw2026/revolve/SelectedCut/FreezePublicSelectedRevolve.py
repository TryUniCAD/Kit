from argparse import ArgumentParser
from hashlib import sha256
from io import BytesIO
from pathlib import Path, PurePosixPath, PureWindowsPath
from subprocess import check_output, run
from tarfile import TarInfo, open as open_tar
import json
import os
import sys

HERE = Path(__file__).resolve()
TOOLS = "re/tooling/sw2026"
WORKER = f"{TOOLS}/revolve/SelectedCut/ProvePublicSelectedRevolve.py"
DISCLOSURE = "re/solidworks/measurements/2026/SdkPublicSelectedRevolveDisclosure01.json"
READER_PROOF = "re/solidworks/measurements/2026/SdkScopedRevolveHeldoutRecheck02.json"
SCHEMA = "kit.sw2026.public-selected-revolve-freeze.v1"
PREFIX = PureWindowsPath(r"C:\KitSdkCandidates")
WRITER = "0cc19e4adcfca7bd55c0ebf0ebf97bf457e234ebe11dd045de07f08a5be43f17"
CANDIDATE = "ecd941c1a9b5a936d26db77efcf68f5ee479457b1e5685c64c004b1b827d6b1a"
NATIVE = "aee4c2213efdd216e35a9c22de36811b83eab06703b9233ef0f06d36619c8084"
READER = "0b041e7b5e75d3a6b06315174d631a6695c6cd5632aa6aca04bfa5c217c5398d"
TOP_TOOLS = ("AuthorCurves.py", "AuthorRevolveFamilies.py", "AuthorRevolveSources.py", "ComparePerpendicularRuntimes.py",
             "InspectFresh.py", "OracleIdentity.py", "RevolveFamilyModel.py", "Swapp.py", "VerifySdkCircleEndRegistration.py")
stage = "capsule"


def require(condition, diagnostic):
    if not condition:
        raise ValueError(diagnostic)


def digest(data):
    return sha256(data).hexdigest()


def checked(path, pin):
    value = path.read_bytes()
    require(not path.is_symlink() and digest(value) == pin, "protected capsule input hash does not match")
    return value


def encode(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def publish(path, value):
    with path.open("xb") as output:
        output.write(value)


def freeze(folder):
    root = HERE.parents[5]

    def git(*args):
        return check_output(("git", *args), cwd=root)

    require(folder.is_absolute() and not folder.exists() and not folder.is_relative_to(root), "use a fresh external capsule")
    revision = git("rev-parse", "HEAD").decode().strip()
    tree = git("rev-parse", f"{revision}:src").decode().strip()
    proof = git("show", f"{revision}:{DISCLOSURE}")
    reader = git("show", f"{revision}:{READER_PROOF}")
    self_raw = git("show", f"{revision}:{HERE.relative_to(root).as_posix()}")
    result = json.loads(proof)
    require(result["passed"] and result["fresh_processes"] == 4 and all(case["fresh_path_and_stream_routes"] == 4
            and case["runtime_writer_input_reads"] == 0 and case["passed"] for case in result["cases"].values())
            and digest(reader) == READER and json.loads(reader)["passed"] and HERE.read_bytes() == self_raw,
            "require the exact public disclosure and protected reader proof")
    tools = git("ls-tree", "-r", "--name-only", revision, f"{TOOLS}/revolve").decode().splitlines()
    tools = sorted({*(name for name in tools if name.endswith((".py", ".json"))), *(f"{TOOLS}/{name}" for name in TOP_TOOLS)})
    require(WORKER in tools, "public worker is missing from the committed source inventory")
    packed = BytesIO()
    source = git("archive", "--format=tar", revision, "src")
    with open_tar(fileobj=BytesIO(source), mode="r:") as sdk, open_tar(fileobj=packed, mode="w:gz") as bundle:
        for member in sdk:
            require(member.isdir() or member.isfile(), "unexpected SDK source archive member")
            bundle.addfile(member, sdk.extractfile(member) if member.isfile() else None)
        for name in tools:
            raw = git("show", f"{revision}:{name}")
            member = TarInfo(name)
            member.size, member.mode = len(raw), 0o644
            bundle.addfile(member, BytesIO(raw))
    code = packed.getvalue()
    files = {"Observe.py": self_raw, "Code.tar.gz": code, "Disclosure.json": proof, "ReaderResult.json": reader}
    record = encode({"schema": SCHEMA, "revision": revision, "source_tree": tree, "writer_freeze_sha256": WRITER,
                     "reader_result_sha256": READER, "without_sealed_inputs": True,
                     "files": {name: digest(value) for name, value in files.items()}})
    folder.mkdir()
    for name, value in files.items():
        publish(folder / name, value)
    publish(folder / "PublicFreeze.json", record)
    return {"freeze_sha256": digest(record), "source_tree": tree, "sealed_sources_opened": 0}


def expand(raw, root):
    with open_tar(fileobj=BytesIO(raw), mode="r:gz") as bundle:
        entries = bundle.getmembers()
        names = {member.name.casefold() for member in entries}
        require(len(names) == len(entries) and all((member.isfile() or member.isdir())
                and not any(part in (".", "..") or ":" in part or "\\" in part for part in PurePosixPath(member.name).parts)
                and not PurePosixPath(member.name).is_absolute()
                and (member.name.startswith("src/") or member.name == "src" or member.name in ("re", "re/tooling", TOOLS)
                     or member.name.startswith(f"{TOOLS}/revolve") or member.name in {f"{TOOLS}/{name}" for name in TOP_TOOLS})
                for member in entries), "unverified public SDK archive member")
        root.mkdir()
        bundle.extractall(root, members=entries, filter="data")


def invoke(script, request, *arguments):
    child = run((sys.executable, "-I", "-B", str(script), *arguments, "--worker"), input=encode(request),
                capture_output=True, timeout=180)
    require(child.returncode == 0 and not child.stderr, "isolated protected SDK comparison failed")
    return json.loads(child.stdout)


def observe(folder, pin):
    global stage
    require(os.name == "nt" and folder == HERE.parent and folder.name.startswith("ScopedRevolvePublicWriter"),
            "run isolated public SDK evaluation on the oracle host")
    manifest = json.loads(checked(folder / "PublicFreeze.json", pin))
    files = {name: checked(folder / name, value) for name, value in manifest["files"].items()}
    require(manifest["schema"] == SCHEMA and manifest["without_sealed_inputs"] and manifest["writer_freeze_sha256"] == WRITER
            and manifest["reader_result_sha256"] == READER and files["Observe.py"] == HERE.read_bytes()
            and digest(files["ReaderResult.json"]) == READER, "unverified protected public capsule")
    disclosure = json.loads(files["Disclosure.json"])
    earlier = folder.parent / "ScopedRevolveHeldoutEval03"
    sys.path.insert(0, str(earlier))
    from EvaluateHeldoutStockCuts import LOCK, LOCK_SHA, verify

    writer_manifest, original_run, frozen = verify(earlier, WRITER)
    sys.path.insert(0, str(frozen / TOOLS / "revolve" / "SelectedCut"))
    from RunScopedRevolveNative import ORACLE_SHA, path_for, source_lock, validate_specs

    private = Path(PREFIX / folder.name)
    private.mkdir()
    root = private / "Code"
    expand(files["Code.tar.gz"], root)
    worker = root / WORKER
    require(worker.is_file(), "public comparison worker is missing from its source capsule")
    stage = "disclosed"
    prototype = frozen / TOOLS / "revolve" / "SelectedCut" / "BuildStockCutSelector.py"
    public_probes = []
    for name, result_pin in disclosure["native_result_sha256"].items():
        packet = folder.parent / name
        result = json.loads(checked(packet / "Inspection" / "Result.json", result_pin))
        recipe = json.loads(checked(packet / "Packet.json", result["packet_sha256"]))
        require(result["passed"] and result["controls_healthy"] and result["oracle_sha256"] == ORACLE_SHA, "public oracle proof failed")
        for case in validate_specs(json.loads(checked(packet / "ModelSpecs.json", recipe["files"]["ModelSpecs.json"]))):
            name = case["name"]
            phase = result["cases"][name]["phases"][0]
            observed = json.loads(checked(packet / "Inspection" / name / "Initial.json", phase["sha256"]))
            locator = str(PureWindowsPath(recipe["guest_workspace"]) / path_for(case))
            stock = invoke(prototype, {"case": case, "epoch": recipe["epoch"], "locator": locator, "policy": "sentinel"})
            require(stock["zero_runtime_reads"], "old disclosed construction lost its guard")
            request = {"case": case, "epoch": recipe["epoch"], "locator": locator, "candidate_sha256": stock["sha256"],
                       "scratch": str(private), "path_routes": False, "observed": observed["reopened"]}
            public_probes.append(invoke(worker, request))
    require(len(public_probes) == 4 and all(result["passed"] for result in public_probes), "public guest preflight failed")

    stage = "protected"
    area = original_run / "CandidatePacket"
    candidate = json.loads(checked(area / "Packet.json", CANDIDATE))
    native = json.loads(checked(area / "Inspection" / "Result.json", NATIVE))
    prior = json.loads(files["ReaderResult.json"])
    require(native["passed"] and native["controls_healthy"] and native["idle_after"] and native["distinct_processes"] == 6
            and native["oracle_sha256"] == ORACLE_SHA and native["packet_sha256"] == CANDIDATE and candidate["freeze_sha256"] == WRITER
            and native["codec_revision"] == candidate["codec_revision"] == writer_manifest["writer_revision"]
            and prior["passed"] and prior["locked_source_sha256"] == LOCK_SHA and prior["candidate_packet_sha256"] == CANDIDATE
            and prior["native_result_sha256"] == NATIVE, "protected generation or native acceptance pin does not match")
    custody = source_lock(checked(frozen / LOCK, LOCK_SHA))
    cases = validate_specs(json.loads(checked(area / "ModelSpecs.json", custody["spec_sha256"])))
    records = {}
    for case, locked in zip(cases, custody["sources"], strict=True):
        name, slot, filename = case["name"], locked["case"], path_for(case)
        native_row = native["cases"][name]
        expected = native_row["candidate_sha256"]
        collected = json.loads(checked(area / "Inspection" / name / "Initial.json", native_row["phases"][0]["sha256"]))
        require(native_row["passed"] and collected["passed"] and prior["cases"][slot]["native"]["passed"]
                and expected == prior["cases"][slot]["candidate_sha256"] == candidate["files"][f"Candidates/{filename}"],
                "sealed candidate no longer matches the measured writer result")
        result = invoke(worker, {"case": case, "epoch": candidate["epoch"], "path_routes": False, "scratch": str(private),
                                 "locator": str(PureWindowsPath(candidate["guest_workspace"]) / filename),
                                 "candidate_sha256": expected, "observed": collected["reopened"]})
        require(result["passed"] and result["sha256"] == expected and result["runtime_writer_input_reads"] == 0
                and result["unexpected_reader_input_reads"] == 0 and result["streams"] == 10, "public exact protected reproduction failed")
        records[slot] = {key: result[key] for key in ("sha256", "streams", "named_stream_routes", "runtime_writer_input_reads",
                                                      "unexpected_reader_input_reads", "writer_refusals", "strict_reader_refusals")}
        records[slot]["cold_native_mass_and_bounds_checks"] = result["cold"]["native_mass_and_bounds_checks"]
        records[slot]["cold_owned_D1s"] = result["cold"]["owned_D1s"]
    value = encode({"schema": "kit.sw2026.public-selected-revolve-protected.v1", "freeze_sha256": pin,
                    "revision": manifest["revision"], "source_tree": manifest["source_tree"], "native_result_sha256": NATIVE,
                    "reader_result_sha256": READER, "locked_source_sha256": LOCK_SHA, "native_original_files_read": 0,
                    "new_oracle_launches": 0, "existing_native_processes": native["distinct_processes"],
                    "public_guest_preflight": len(public_probes), "protected_cases": records, "passed": True})
    publish(folder / "PublicResult.json", value)
    return {"result_sha256": digest(value), "protected_cases": len(records), "passed": True}


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("action", choices=("freeze", "observe"))
    parser.add_argument("folder", type=Path)
    parser.add_argument("--pin")
    args = parser.parse_args()
    if args.action == "freeze":
        result = freeze(args.folder)
    else:
        try:
            result = observe(args.folder, args.pin)
        except Exception as error:
            print(json.dumps({"passed": False, "stage": stage, "error_type": type(error).__name__}))
            raise SystemExit(1) from None
    print(json.dumps(result, sort_keys=True))
