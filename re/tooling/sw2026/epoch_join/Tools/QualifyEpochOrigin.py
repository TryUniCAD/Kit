from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(value):
    return sha256(value).hexdigest()


def encode(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def checked(root, row):
    relative = Path(row.get("relative_path", row["path"]))
    path = root / relative
    require(not relative.is_absolute() and ".." not in relative.parts and not path.is_symlink()
            and path.resolve(strict=True).is_relative_to(root.resolve()), "epoch join input escaped its declared root")
    raw = path.read_bytes()
    require(len(raw) == row["bytes"] and digest(raw) == row["sha256"], "epoch join input custody differs")
    return path


def verify_source(candidate, expected):
    raw = (candidate / "SourceManifest.json").read_bytes()
    require(digest(raw) == expected, "epoch join SDK source manifest differs")
    manifest = json.loads(raw)
    root = (candidate / "CodeRoot").resolve(strict=True)
    names = set()
    for row in manifest["files"]:
        checked(root, row)
        require(row["path"] not in names, "epoch join SDK source has duplicate members")
        names.add(row["path"])
    require(len(names) == manifest["file_count"]
            and names == {str(path.relative_to(root)) for path in root.rglob("*") if path.is_file()},
            "epoch join SDK source membership differs")
    return manifest


def main():
    parser = argparse.ArgumentParser(description="Independent exact typed origin, component, configuration and clock join for an immutable epoch packet")
    parser.add_argument("candidate", type=Path)
    parser.add_argument("packet", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--method-sha256", required=True)
    args = parser.parse_args()
    method_path = Path(__file__).resolve().parent.parent / "MethodManifest.json"
    method_raw = method_path.read_bytes()
    require(digest(method_raw) == args.method_sha256, "epoch join method manifest differs")
    method = json.loads(method_raw)
    method_root = method_path.parent
    for row in method["tools"]:
        checked(method_root, row)
    require(Path(__file__).resolve() == method_root / "Tools/QualifyEpochOrigin.py", "epoch join controller location differs")
    sys.path.append(str(Path(__file__).resolve().parent))
    from EpochJoinRules import check_row
    source = verify_source(args.candidate, method["source_manifest_sha256"])
    packet_raw = args.packet.read_bytes()
    require(digest(packet_raw) == method["packet_sha256"], "epoch packet changed")
    packet = json.loads(packet_raw)
    require(packet["source_manifest_sha256"] == method["source_manifest_sha256"], "epoch packet SDK source differs")
    root = args.packet.parent.resolve(strict=True)
    for row in (*packet["tools"].values(), *packet["host_tools"].values(), packet["control"], *packet["custody"]):
        checked(root, row)
    native_raw = (root / "Inspection/Result.json").read_bytes()
    require(digest(native_raw) == method["native_result_sha256"], "epoch native result changed")
    native = json.loads(native_raw)
    require(native["packet_sha256"] == method["packet_sha256"] and native["passed"] is True
            and native["controls_healthy"] is True and native["native_lifecycle_passed"] is True
            and native["distinct_native_processes"] == 18 and len(native["phases"]) == 18,
            "epoch join has no complete controlled native lifecycle")
    clock_raw = (root / "ClockObservation01.json").read_bytes()
    require(digest(clock_raw) == method["clock_observation_sha256"], "epoch clock observation changed")
    clock = json.loads(clock_raw)
    require(clock["data_collected"] is True and clock["packet_sha256"] == method["packet_sha256"]
            and clock["native_result_sha256"] == method["native_result_sha256"]
            and clock["source_manifest_sha256"] == method["source_manifest_sha256"], "epoch clock source binding differs")
    clocks = {row["case"]: row for row in clock["cases"]}
    require(len(packet["cases"]) == len(clocks) == 4 and not args.output.exists(), "epoch join case set or output differs")
    args.output.mkdir(parents=True)
    report = {"schema": "kit.sw2026.epoch-typed-origin-join.v1", "method_sha256": args.method_sha256,
              "source_manifest_sha256": method["source_manifest_sha256"], "sdk_source_files": source["file_count"],
              "packet_sha256": method["packet_sha256"], "native_result_sha256": method["native_result_sha256"],
              "clock_observation_sha256": method["clock_observation_sha256"], "states": [], "passed": False,
              "disclosed_epoch_lifecycle_qualified": False, "heldout_acceptance": False,
              "original_source_output_verdict_changed": False, "public_constructor_expansion_qualified": False,
              "vm_calls": False, "hidden_inputs_read": False}
    result_path = args.output / "Result.json"
    def checkpoint():
        result_path.write_bytes(encode(report))
    checkpoint()
    states = (("constructed", None), ("initial", "open-save"), ("initial_reopen", "reopen"),
              ("edited", "edit-move-save"), ("edited_reopen", "reopen-edited"))
    for state, phase in states:
        pairs = []
        expected = {}
        for case in packet["cases"]:
            name = case["name"]
            if phase is None:
                files = {key: case["files"][key] for key in ("drawing", "child")}
                expected[name] = case["generated_profile"]["child_origin_id"]
                clock_state = clocks[name]["constructed"]
            else:
                native_row = native["phases"][name + "/" + phase]
                require(native_row["passed"] is True, "epoch join native phase is incomplete")
                files = {"drawing": native_row["drawing_file"], "child": native_row["child_file"]}
                expected[name] = native_row["saved"]["child"]["profile_ids"]["origin"]
                clock_state = clocks[name]["phases"][phase]
            entries = {}
            for kind, item in files.items():
                path = checked(root, item)
                entries[kind] = {"path": str(path), "bytes": item["bytes"], "sha256": item["sha256"]}
                require(item["sha256"] == clock_state[kind + "_sha256"], "clock and origin join select different actual files")
            pairs.append({"case": name, "role": state, **entries, "orientation": case["view"]["orientation"],
                          "declared_expected_native_resolved_path": case["paths"]["child"]})
        pairs_path = args.output / (state + "Pairs.json")
        pairs_path.write_bytes(encode({"schema": "kit.sw2026.disclosed-profile-child-pairs.v1", "pairs": pairs}))
        observed_path = args.output / (state + "Profiles.json")
        observer = method_root / "Tools/InspectEpochProfileChild.py"
        process = subprocess.run([sys.executable, "-I", "-B", str(observer), str(args.candidate), str(pairs_path),
                                  str(observed_path), "--manifest-sha256", method["source_manifest_sha256"],
                                  "--pairs-sha256", digest(pairs_path.read_bytes())], capture_output=True, timeout=300)
        (args.output / (state + ".stdout.txt")).write_bytes(process.stdout)
        (args.output / (state + ".stderr.txt")).write_bytes(process.stderr)
        observation = json.loads(observed_path.read_bytes()) if observed_path.is_file() else None
        batch = {"state": state, "native_phase": phase, "return_code": process.returncode,
                 "pairs_sha256": digest(pairs_path.read_bytes()), "stdout_sha256": digest(process.stdout),
                 "stderr_sha256": digest(process.stderr), "rows": [], "passed": False}
        report["states"].append(batch)
        if observation is None:
            batch["diagnostic"] = "independent profile observer produced no report"
            checkpoint()
            continue
        batch["raw_report_sha256"] = digest(observed_path.read_bytes())
        batch["data_collected"] = observation.get("data_collected") is True
        batch["source_immutable"] = observation.get("source_immutable") is True
        lookup = {case["name"]: case for case in packet["cases"]}
        seen = set()
        for row in observation["cases"]:
            name = row["case"]
            require(name in lookup and name not in seen, "independent profile observation case membership differs")
            seen.add(name)
            clock_state = clocks[name]["constructed"] if phase is None else clocks[name]["phases"][phase]
            try:
                joined = check_row(row, lookup[name], expected[name], clock_state)
            except (KeyError, TypeError, ValueError) as error:
                joined = {"passed": False, "diagnostic": {"exception": type(error).__name__, "message": str(error)},
                          "observer_failure": row.get("failure")}
            batch["rows"].append({"case": name, "state": state, "actual_native_origin_id": expected[name], **joined})
        batch["passed"] = (process.returncode == 0 and batch["data_collected"] and batch["source_immutable"]
                           and len(seen) == 4 and all(row["passed"] for row in batch["rows"]))
        checkpoint()
    verify_source(args.candidate, method["source_manifest_sha256"])
    for row in method["tools"]:
        checked(method_root, row)
    require(digest(args.packet.read_bytes()) == method["packet_sha256"]
            and digest((root / "Inspection/Result.json").read_bytes()) == method["native_result_sha256"]
            and digest((root / "ClockObservation01.json").read_bytes()) == method["clock_observation_sha256"],
            "epoch raw artifacts changed during the independent join")
    report["passed"] = len(report["states"]) == 5 and all(row["passed"] for row in report["states"])
    report["disclosed_epoch_lifecycle_qualified"] = report["passed"]
    report["complete_joined_pairs"] = sum(row["passed"] for batch in report["states"] for row in batch["rows"])
    report["source_and_raw_immutable"] = True
    checkpoint()
    print(json.dumps({"passed": report["passed"], "complete_joined_pairs": report["complete_joined_pairs"],
                      "result_sha256": digest(result_path.read_bytes()), "heldout_acceptance": False}))
    return 0 if report["passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
