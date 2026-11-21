from argparse import ArgumentParser
from base64 import b64decode
from pathlib import Path, PureWindowsPath
from subprocess import check_output, run
import json
import sys

from AuditNestedNeutralComposition import CASES, HERE as WORKER, ROOT, checked, digest, require
from InspectSdkNestedAssembly import ORACLE, SCHEMA, SOURCE_LOCK, TOOLS
from PrepareSdkNestedTrial import windows_path, write
from SdkNestedExpectations import prediction, verify_prediction


def git(*arguments):
    return check_output(("git", *arguments), cwd=ROOT)


def set_destination(request, folder):
    native = PureWindowsPath(r"\\Mac\Home\Documents\UniCAD\Oracle121Takeover") / folder.name / "GeneratedInput"
    for row in request["definitions"]:
        payload = row["request"]
        settings = payload["settings"] if row["kind"] == "part" else payload
        old = PureWindowsPath(settings["output"]["path_name"])
        settings["output"]["path_name"] = str(native / old.name)
    return native


def build(request, target):
    raw = (json.dumps({"request": request, "stage_bundle": True}, allow_nan=False) + "\n").encode()
    result = run((sys.executable, "-I", "-B", str(WORKER), "--worker"), input=raw,
                 capture_output=True, timeout=180)
    require(result.returncode == 0 and not result.stderr, result.stderr.decode(errors="replace")[-2400:])
    record = json.loads(result.stdout)
    require(record["passed"] and record["runtime_file_reads"] == 0, "guarded neutral bundle did not qualify")
    outputs = record.pop("outputs")
    return {"worker_pid": record["worker_pid"], "passed": True, "runtime_input_file_reads": 0,
            "sdk_runtime_research_imports": 0, "documents": {
                key: outputs[row["file"]] for key, row in target["definitions"].items()
            }}


def stage(source, folder, edit):
    require(source.name in CASES and folder.is_absolute() and source.parent == folder.parent
            and not folder.exists() and not folder.is_relative_to(ROOT), "choose a new sibling of the disclosed trial")
    fixture_pin = CASES[source.name]
    old = json.loads(checked(source / "Fixture.json", fixture_pin))
    packet_raw = (source / "Packet.json").read_bytes()
    packet = json.loads(packet_raw)
    require(packet["fixture_sha256"] == fixture_pin and packet["oracle_sha256"] == ORACLE
            and packet["source_lock_sha256"] == SOURCE_LOCK and set(packet["tools_sha256"]) == set(TOOLS),
            "disclosed native fixture lacks its ordinary oracle")
    request = json.loads(checked(source / "NeutralRequest.json", old["request_sha256"]))
    native = set_destination(request, folder)
    expected = prediction(request, "plate", edit)
    require(verify_prediction(request, expected) == native, "independent prediction did not bind the new working directory")
    revision = git("rev-parse", "HEAD").decode().strip()
    paths = tuple(path.relative_to(ROOT).as_posix() for path in (WORKER, Path(__file__).resolve()))
    witness = {"revision": revision, "sdk_tree": git("rev-parse", f"{revision}:src").decode().strip(),
               "tool_sha256": {name: digest(git("show", f"{revision}:{name}")) for name in paths}}
    require(not git("diff", "--name-only", revision, "--", "src", *paths)
            and all(digest((ROOT / name).read_bytes()) == witness["tool_sha256"][name] for name in paths),
            "native packet requires the committed public preparation and measurement source")
    folder.mkdir()
    manifest = write(folder / "SourceManifest.json", witness)
    request_sha = write(folder / "NeutralRequest.json", request)
    prediction_sha = write(folder / "Prediction.json", expected)
    first, second = (build(request, expected) for _ in range(2))
    require(first["worker_pid"] != second["worker_pid"] and first["documents"] == second["documents"],
            "independent neutral builds differ")
    require(not git("diff", "--name-only", revision, "--", "src", *paths), "SDK source changed during packet generation")
    builds = {name: write(folder / (name + ".stdout"), row) for name, row in (("BuildA", first), ("BuildB", second))}
    output = folder / "FrozenGenerated"
    output.mkdir()
    files = {}
    for key, row in first["documents"].items():
        file = expected["definitions"][key]["file"]
        raw = b64decode(row["blob"], validate=True)
        require(len(raw) == row["bytes"] and digest(raw) == row["sha256"] and PureWindowsPath(row["native_path"]) == native / file,
                "guarded bundle bytes or file identity do not match")
        with (output / file).open("xb") as stream:
            stream.write(raw)
        files[key] = {"file": file, "encoded_path": str(native / file), "bytes": len(raw), "sha256": digest(raw)}
    proof = write(folder / "SourceProcessResult.json", {"source_manifest_sha256": manifest, "passed": True,
                  "runtime_input_file_reads": 0, "heldout_inputs_read": 0, "native_processes_started": 0,
                  "native_acceptance": False, "prior_disclosed_packet_sha256": digest(packet_raw)})
    with (folder / "SourceLock.json").open("xb") as target:
        target.write(checked(source / "SourceLock.json", SOURCE_LOCK))
    frozen = write(folder / "Fixture.json", {"schema": "kit.sw2026.sdk-nested-native-fixture.v1",
                   "source_manifest_sha256": manifest, "source_process_result_sha256": proof,
                   "request_sha256": request_sha, "prediction_sha256": prediction_sha, "native_acceptance": False,
                   "build_sha256": builds, "files": files, "neutral_preparation_revision": revision,
                   "typed_stream_round_trips_per_build": sum(len(row["streams"]) for row in first["documents"].values())})
    tools = folder / "Tools"
    tools.mkdir()
    for name, pin in packet["tools_sha256"].items():
        with (tools / name).open("xb") as destination:
            destination.write(checked(source / "Tools" / name, pin))
    with (folder / "ToolsManifest.json").open("xb") as destination:
        destination.write(checked(source / "ToolsManifest.json", packet["tools_manifest_sha256"]))
    observer_digest = write(folder / "Packet.json", {**packet, "schema": SCHEMA, "fixture_sha256": frozen})
    observer = tools / "InspectSdkNestedAssembly.py"
    proof_path = folder / "Packet.json"
    process = run((sys.executable, "-B", str(observer), "verify", str(proof_path), "--packet-sha256", observer_digest),
                  capture_output=True, text=True, timeout=90)
    require(process.returncode == 0 and not process.stderr, process.stderr[-2500:])
    return {"packet_sha256": observer_digest, "fixture_sha256": frozen, "source_manifest_sha256": manifest,
            "observer": windows_path(observer), "packet": windows_path(proof_path), "writer_revision": revision,
            "typed_streams": sum(len(row["streams"]) for row in first["documents"].values()), "passed": True}


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--edit-depth-m", type=float, default=0.011375)
    args = parser.parse_args()
    print(json.dumps(stage(args.source.resolve(strict=True), args.output, args.edit_depth_m), sort_keys=True))
