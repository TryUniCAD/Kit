from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from shutil import copyfile

from AuthorCurves import Recorder, digest, require, write_json
from AuthorNestedAssemblySources import file_paths, reopen_case
from NestedAssemblySourcePlan import CONTROL_SHA, ORACLE, PARAMETERS, TOOL_FILES, checked, validate_case
from ReplayIndexedAssemblyProgress import DISCLOSED


SCRIPT = Path(__file__).resolve()
TOOLS = (*TOOL_FILES, "ReplayIndexedAssemblyProgress.py", SCRIPT.name)
SCHEMA = "kit.sw2026.disclosed-nested-reopen-replay.v1"
AUTHORED = {
    "N01NestedSingle": "9b4b1f3da116761ff27781fedaabc64e89c88bd385868085f4f5204c9686d330",
    "N02MixedRepeated": "66306b78ae69ef6160d54f5f4fc76b0a41bfa9b976145cdad1b4727215de0b1f",
}
SOURCE = Path("NestedAssemblySource01") / "Results"


def source_cases(root):
    require(root == root.resolve(strict=True) and tuple(root.parts[-2:]) == SOURCE.parts, "use the exact first disclosed-source directory")
    cases = {}
    for name, sha in AUTHORED.items():
        directory = root / name
        source = checked(directory / "Author.json", sha, directory)
        checked(directory / "Reopen.json", DISCLOSED[name], directory)
        authored = json.loads(source.read_bytes())
        case = validate_case(authored["job"]["case"])
        result = authored["result"]
        require(authored["passed"] and result["passed"] and result["native_files_match_persisted"] and
                case["name"] == name and case["split"] == "discovery" and authored["job"]["mode"] == "author", "unexpected disclosed source phase")
        paths = file_paths(directory / "Author", case)
        saved = result["saved_files"]
        require(set(saved) == set(paths), "the original case does not contain its complete dependency closure")
        for definition, path in paths.items():
            info = saved[definition]
            require(info["status"] == [True, 0, 0] and checked(path, info["sha256"], directory).stat().st_size == info["bytes"],
                    "disclosed saved sibling differs from its author receipt")
        cases[name] = (case, paths, result)
    return cases


def load(path, sha):
    root = path.parent
    require(path.name == "Replay.json" and checked(path, sha, root) == path, "nested replay manifest is not pinned")
    job = json.loads(path.read_bytes())
    require(job["schema"] == SCHEMA and job["read_only"] is True and job["heldout_inputs_read"] == 0 and
            job["oracle_sha256"] == ORACLE and job["control_sha256"] == CONTROL_SHA and job["author_records"] == AUTHORED and
            job["previous_reopen_records"] == DISCLOSED, "unexpected disclosed replay scope")
    tools = (root / "Tools").resolve(strict=True)
    require(tools == SCRIPT.parent and tools.is_relative_to(root) and set(job["tools_sha256"]) == set(TOOLS), "run the exact frozen replay tooling")
    for name, digest_value in job["tools_sha256"].items():
        checked(tools / name, digest_value, tools)
    source = (root.parent / SOURCE).resolve(strict=True)
    require(source == root.parent / SOURCE and not source.is_relative_to(root), "replay source must remain at its exact original path")
    return job, checked(root / "Seed.SLDPRT", CONTROL_SHA, root), source_cases(source)


def prepare(args):
    root = args.replay.resolve()
    require(not root.exists() and root.parent.is_dir() and not root.is_relative_to(SCRIPT.parents[3]), "choose an unused private nested replay deck")
    require(args.source.resolve(strict=True) == root.parent / SOURCE, "the replay deck must be a peer of NestedAssemblySource01")
    source_cases(args.source.resolve(strict=True))
    seed = checked(args.seed, CONTROL_SHA)
    root.mkdir()
    tools = root / "Tools"
    tools.mkdir()
    copyfile(seed, root / "Seed.SLDPRT")
    hashes = {}
    for name in TOOLS:
        target = tools / name
        copyfile(SCRIPT.parent / name, target)
        hashes[name] = digest(target)
    path = root / "Replay.json"
    write_json(path, {"schema": SCHEMA, "oracle_sha256": ORACLE, "control_sha256": CONTROL_SHA, "read_only": True,
                      "heldout_inputs_read": 0, "author_records": AUTHORED, "previous_reopen_records": DISCLOSED,
                      "tools_sha256": hashes})
    sha = digest(path)
    subprocess.run([sys.executable, "-B", str(tools / SCRIPT.name), "verify", str(path), "--replay-sha256", sha],
                   capture_output=True, check=True, timeout=25)
    return {"replay": str(path), "replay_sha256": sha, "tools_sha256": hashes}


def inspect_case(case, paths, prior, output):
    import Swapp
    from AuthorCurves import CurveAuthor
    from ObserveAssemblyLoad import AssemblyLoadMonitor
    from OracleIdentity import application_identity

    record = Recorder(output / (case["name"] + ".json"), {"case": case, "read_only": True})
    result = {"name": case["name"], "passed": False}
    controller = None
    with AssemblyLoadMonitor() as monitor:
        try:
            record.call("verify idle oracle", Swapp.sweep)
            controller = record.call("launch fresh owned oracle", Swapp.Sw)
            identity = record.call("verify executable version and SHA-256", application_identity, controller.app)
            result["oracle_identity"] = identity
            require(identity["version_matches"] and identity["sha256"] == ORACLE and controller.revision == "34.5.2", "unexpected pinned executable")
            author = CurveAuthor(controller.app, record, Swapp)
            reopen_case(author, controller, case, paths, prior, result)
            result["passed"] = True
        except Exception as error:
            record.failure(error)
            result["exception"] = repr(error)
        finally:
            if controller is not None:
                controller.close()
                result["controller_diagnostics"] = controller.diagnostics
    result["dialogs"] = monitor.log
    result["progress_windows"] = monitor.progress
    result["source_files_unchanged"] = all(path.is_file() and digest(path) == prior["saved_files"][name]["sha256"] for name, path in paths.items())
    result["passed"] = bool(result["passed"] and result["source_files_unchanged"] and not result["dialogs"] and not result.get("controller_diagnostics"))
    record.data.update(result=result, passed=result["passed"], finished_at=time.time())
    record.flush()
    return result


def run(path, sha):
    from InspectFresh import healthy, inspect

    job, seed, sources = load(path, sha)
    output = path.parent / "Inspection"
    output.mkdir(exist_ok=False)
    target = output / "DisclosedNestedReopenResults.json"
    result = {"schema": SCHEMA, "replay_sha256": sha, "oracle_sha256": ORACLE, "tools_sha256": job["tools_sha256"],
              "original_reopen_records": DISCLOSED, "heldout_inputs_read": 0, "writer_output_count": 0,
              "read_only": True, "passed": False, "phases": [], "started_at": time.time()}

    def control(label):
        row = {"name": label, "mode": "control", "passed": False}
        result["phases"].append(row)
        inspect(seed, result=row, parameter_names=PARAMETERS)
        row["passed"] = bool(healthy(row) and row.get("oracle_identity", {}).get("sha256") == ORACLE and row["sha256"] == CONTROL_SHA)
        write_json(target, result)
        return row["passed"]

    try:
        if control("Before"):
            for case, paths, prior in sources.values():
                row = inspect_case(case, paths, prior, output)
                result["phases"].append(row | {"mode": "reopen"})
                write_json(target, result)
    except Exception as error:
        result["exception"] = repr(error)
    finally:
        try:
            control("After")
        except Exception as error:
            result["final_control_exception"] = repr(error)
        phases = result["phases"]
        processes = {row.get("oracle_identity", {}).get("process_creation_filetime") for row in phases}
        result["distinct_processes"] = sum(type(value) is int and value > 0 for value in processes)
        result["input_files_unchanged"] = digest(seed) == CONTROL_SHA and all(
            source.is_file() and digest(source) == prior["saved_files"][name]["sha256"]
            for _, paths, prior in sources.values() for name, source in paths.items())
        result["controls_healthy"] = [row["passed"] for row in phases if row["mode"] == "control"] == [True, True]
        result["passed"] = bool(result["input_files_unchanged"] and result["controls_healthy"] and
                                len(phases) == result["distinct_processes"] == 4 and all(row["passed"] for row in phases) and "exception" not in result)
        result["finished_at"] = time.time()
        write_json(target, result)
    return result


def main():
    parser = argparse.ArgumentParser(description="Freeze or replay the exact two disclosed nested assembly reopens without source changes")
    modes = parser.add_subparsers(dest="mode", required=True)
    prepare_args = modes.add_parser("prepare")
    for label in ("source", "seed", "replay"):
        prepare_args.add_argument(label, type=Path)
    for mode in ("verify", "run"):
        command = modes.add_parser(mode)
        command.add_argument("manifest", type=Path)
        command.add_argument("--replay-sha256", required=True)
    args = parser.parse_args()
    if args.mode == "prepare":
        print(json.dumps(prepare(args), sort_keys=True))
        return 0
    path = args.manifest.resolve(strict=True)
    if args.mode == "verify":
        load(path, args.replay_sha256)
        print(json.dumps({"verified_replay": args.replay_sha256}))
        return 0
    result = run(path, args.replay_sha256)
    print(json.dumps({key: result[key] for key in ("passed", "controls_healthy", "distinct_processes")}))
    return int(not result["passed"])


if __name__ == "__main__":
    raise SystemExit(main())
