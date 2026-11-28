from __future__ import annotations

import argparse
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path, PureWindowsPath
import re
import shutil
import subprocess
import sys
import time
from types import SimpleNamespace

COMPARATOR = "38db51428485c1c0b7075cedfe44f76b99f0bf36d0a8c5300141cbb299cacfa7"
TOOLS = ("RunBlankDrawingComparison01.py", "BlankDrawingComparison01.py", "InspectDrawingCache.py", "AuthorDrawingSources.py", "AuthorCurves.py", "DrawingCacheCases.py", "OracleIdentity.py", "Swapp.py")
BASES = ("ControlBefore", "Slot01/Source", "Slot01/Generated", "Slot02/Source", "Slot02/Generated", "ControlAfter")
STAGES = ("OpenEditSave", "FreshReopen")
SOURCE_ROOT = r"C:\KitBlankDrawingSource121"


def require(value, label):
    if not value:
        raise ValueError(label)


def fingerprint(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def load(row):
    path = Path(row["path"])
    require(path.is_absolute() and not path.is_symlink() and fingerprint(path) == row["sha256"], "pinned file changed")
    return json.loads(path.read_bytes())


def write_new(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, indent=2, allow_nan=False) + "\n")
    return {"path": str(path), "sha256": fingerprint(path)}


def comparison():
    path = Path(__file__).with_name("BlankDrawingComparison01.py")
    require(fingerprint(path) == COMPARATOR, "original comparator changed")
    spec = importlib.util.spec_from_file_location("frozen_blank_comparison", path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def verify_job(path, expected):
    require(os.name == "nt", "native observation is guest-only")
    job = load({"path": str(path), "sha256": expected})
    require(job["schema"] == "kit.sw2026.blank-drawing-native-job.v1" and job["source_root"] == SOURCE_ROOT, "native job scope changed")
    require(job["phase_order"] == [base + "/" + stage for base in BASES for stage in STAGES], "phase order changed")
    require(Path(job["guest_python"]).resolve() == Path(sys.executable).resolve() and 60 <= job["phase_timeout_seconds"] <= 600, "worker runtime or bound differs")
    directory = Path(__file__).resolve().parent
    manifest = load(job["tools"])
    require(manifest["schema"] == "kit.sw2026.blank-drawing-native-tools.v1" and set(manifest["tools_sha256"]) == set(TOOLS), "native tool closure changed")
    for name, digest in manifest["tools_sha256"].items():
        require(fingerprint(directory / name) == digest, "native tool changed")
    code = comparison()
    bound, locked = code.binding(Path(job["binding"]["path"]), job["binding"]["sha256"])
    require(bound["artifacts"]["native_observer_manifest"]["sha256"] == job["tools"]["sha256"], "observer was not bound before intent release")
    require(job["control"]["sha256"] == code.CONTROL, "wrong pristine control identity")
    output = PureWindowsPath(job["output_root"])
    require(output.is_absolute() and output.drive.upper() == "C:" and ".." not in output.parts and not output.is_relative_to(PureWindowsPath(SOURCE_ROOT)), "use unused separate guest-local output")
    return code, job, bound, locked


def generation_gate(code, job, bound, locked, check_payloads):
    value = load(job["generation"])
    require(value["schema"] == "kit.sw2026.blank-drawing-generation-freeze.v1" and value["method_binding_sha256"] == job["binding"]["sha256"], "wrong generation freeze")
    require(value["native_payload_reads"] == 0 and value["all_outputs_frozen_before_native_attach"] is True and list(value["slots"]) == list(code.SLOTS), "generation access order differs")
    predictions, outputs = {}, {}
    for slot in code.SLOTS:
        row = value["slots"][slot]
        require(row["intent_sha256"] == locked["slots"][slot]["intent_sha256"], "wrong original intent hash")
        predictions[slot] = code.load(row["prediction"])
        require(predictions[slot]["schema"] == "kit.sw2026.blank-drawing-prediction.v1" and predictions[slot]["slot"] == slot and predictions[slot]["method_binding_sha256"] == job["binding"]["sha256"] and predictions[slot]["intent_sha256"] == row["intent_sha256"], "prediction identity differs")
        builds = row["builds"]
        require([item["route"] for item in builds] == ["extension", "solidworks.slddrw"], "ordinary public routes differ")
        require(len({item["target_path"] for item in builds}) == 1 and bool(builds[0]["target_path"]), "matching output target required")
        for item in builds:
            require(item["writer_epoch"] == bound["writer_epoch"] and item["explicit_options_sha256"] == bound["artifacts"]["explicit_options"]["sha256"] and item["writer_manifest_sha256"] == bound["artifacts"]["writer_manifest"]["sha256"], "writer closure or settings changed")
            require(item["data_file_reads"] == item["native_template_reads"] == item["cad_runtime_calls"] == 0 and item["dropped"] == [], "external data, CAD or dropped intent in build")
            require(item["atomic_write_verified"] is True and item["no_overwrite_verified"] is True, "file writer behavior not verified")
        require(builds[0]["output"]["sha256"] == builds[1]["output"]["sha256"], "independent output hashes differ")
        if check_payloads:
            first, second = (code.pinned(item["output"]) for item in builds)
            require(first and first == second, "independent output bytes differ")
        outputs[slot] = builds[0]["output"]
    return predictions, outputs


def verify_gate(path, expected, job, job_sha):
    value = load({"path": str(path), "sha256": expected})
    require(value["schema"] == "kit.sw2026.blank-drawing-native-access-gate.v1" and value["passed"] is True and value["job_sha256"] == job_sha and value["method_binding_sha256"] == job["binding"]["sha256"] and value["generation_sha256"] == job["generation"]["sha256"] and value["tools_sha256"] == job["tools"]["sha256"] and value["all_generated_payloads_verified"] is True and value["native_source_reads_before_gate"] == 0, "original access gate is not qualified")


def expected_for(code, base, predictions):
    slot = base.split("/")[0]
    if slot in code.SLOTS:
        return predictions[slot]
    return {"initial": code.snapshot("Sheet1", [1, 1], 11 * 0.0254, 8.5 * 0.0254), "edited": code.snapshot("Sheet1", [3, 2], 11 * 0.0254, 8.5 * 0.0254), "tree": code.tree("Sheet1")}


def native_input(code, job, locked, outputs, base):
    slot = base.split("/")[0]
    if slot not in code.SLOTS:
        return job["control"]
    if base.endswith("/Source"):
        return {"path": str(Path(job["source_root"]) / slot / "Native" / "Source.SLDDRW"), "sha256": locked["slots"][slot]["source_sha256"]}
    return outputs[slot]


def worker(args):
    code, job, bound, locked = verify_job(args.job, args.job_sha256)
    verify_gate(args.gate, args.gate_sha256, job, args.job_sha256)
    predictions, outputs = generation_gate(code, job, bound, locked, False)
    base, stage = args.phase.rsplit("/", 1)
    wanted = expected_for(code, base, predictions)
    output = Path(job["output_root"])
    source = native_input(code, job, locked, outputs, base)
    if stage == "FreshReopen":
        prior = load({"path": str(output / "Workers" / (base.replace("/", "_") + "_OpenEditSave.json")), "sha256": args.prior_sha256})
        require(prior["passed"] is True and prior["name"] == base + "/OpenEditSave", "fresh reopen prerequisite failed")
        original = load(prior["record"])["result"]
        source = {"path": str(output / "Native" / base / "OpenEditSave" / "EditedDrawing.SLDDRW"), "sha256": original["derivative_sha256"]}
    code.pinned(source)
    import Swapp
    from InspectDrawingCache import phase
    from OracleIdentity import application_identity

    result = phase(Swapp, application_identity, directory=output / "Native" / args.phase, native=Path(source["path"]), expected_hash=source["sha256"], expected=wanted["initial"] if stage == "OpenEditSave" else wanted["edited"], tree=wanted["tree"], oracle_sha=code.ORACLE, edit=stage == "OpenEditSave", edited_ratio=wanted["edited"]["sheet_properties"][2:4])
    record = {"path": str(output / "Native" / args.phase / "Record.json"), "sha256": result["record_sha256"]}
    require(fingerprint(Path(record["path"])) == record["sha256"], "native record changed")
    return {"name": args.phase, "passed": result["passed"], "input_sha256": source["sha256"], "record": record}


def run(args):
    code, job, bound, locked = verify_job(args.job, args.job_sha256)
    generation_gate(code, job, bound, locked, True)
    output = Path(job["output_root"])
    output.mkdir(parents=True, exist_ok=False)
    gate = write_new(output / "AccessGate.json", {"schema": "kit.sw2026.blank-drawing-native-access-gate.v1", "passed": True, "job_sha256": args.job_sha256, "method_binding_sha256": job["binding"]["sha256"], "generation_sha256": job["generation"]["sha256"], "tools_sha256": job["tools"]["sha256"], "all_generated_payloads_verified": True, "native_source_reads_before_gate": 0})
    phases, statuses = [], []
    report = {"schema": "kit.sw2026.blank-drawing-native-run.v1", "job_sha256": args.job_sha256, "access_gate": gate, "passed": False, "statuses": statuses, "full_source_semantics_qualified": False}

    def perform(name, prior=None):
        target = output / "Workers" / (name.replace("/", "_") + ".json")
        command = [job["guest_python"], "-B", str(Path(__file__).resolve()), "worker", "--job", str(args.job), "--job-sha256", args.job_sha256, "--phase", name, "--gate", gate["path"], "--gate-sha256", gate["sha256"]]
        if prior is not None:
            command += ["--prior-sha256", prior["sha256"]]
        status = {"name": name, "passed": False, "started_at": time.time()}
        try:
            completed = subprocess.run(command, capture_output=True, text=True, timeout=job["phase_timeout_seconds"], check=False)
            status["worker_exit_code"] = completed.returncode
            status["worker_stdout_sha256"] = sha256(completed.stdout.encode()).hexdigest()
            status["worker_stderr_sha256"] = sha256(completed.stderr.encode()).hexdigest()
            if target.is_file():
                reference = {"path": str(target), "sha256": fingerprint(target)}
                item = load(reference)
                require(item["name"] == name, "worker phase identity changed")
                status["worker_record"] = reference
                status["passed"] = completed.returncode == 0 and item["passed"] is True
                if "record" in item:
                    phases.append({key: item[key] for key in ("name", "input_sha256", "record")})
            else:
                status["failure_kind"] = "worker_record_absent"
        except subprocess.TimeoutExpired:
            status["failure_kind"] = "worker_timeout_no_native_process_was_killed"
        except Exception as error:
            status["failure_kind"] = type(error).__name__
        raw_record = output / "Native" / name / "Record.json"
        if raw_record.is_file():
            status["raw_record"] = {"path": str(raw_record), "sha256": fingerprint(raw_record)}
        status["finished_at"] = time.time()
        statuses.append(status)
        write_new(output / "Progress" / (str(len(statuses)).zfill(2) + ".json"), status)
        return status

    def lifecycle(base):
        first = perform(base + "/OpenEditSave")
        if not first["passed"]:
            return False
        return perform(base + "/FreshReopen", first["worker_record"])["passed"]

    try:
        if lifecycle("ControlBefore"):
            for base in BASES[1:-1]:
                if not lifecycle(base):
                    break
    except Exception as error:
        report["pipeline_error_type"] = type(error).__name__
    finally:
        try:
            report["trailing_control_passed"] = lifecycle("ControlAfter")
        except Exception as error:
            report["trailing_control_error_type"] = type(error).__name__
        try:
            _, outputs = generation_gate(code, job, bound, locked, True)
            for slot in code.SLOTS:
                code.pinned(native_input(code, job, locked, outputs, slot + "/Source"))
                code.pinned({"path": str(Path(job["source_root"]) / slot / "edit" / "EditedDrawing.SLDDRW"), "sha256": locked["slots"][slot]["edited_sha256"]})
            code.pinned(job["control"])
            immutable = True
        except Exception as error:
            immutable = False
            report["immutability_error_type"] = type(error).__name__
        observations = write_new(output / "Observations.json", {"schema": "kit.sw2026.blank-drawing-native-observations.v1", "generation_sha256": job["generation"]["sha256"], "inputs_immutable": immutable, "phases": phases})
        report["observations"] = observations
        try:
            comparison_args = SimpleNamespace(binding_sha256=job["binding"]["sha256"], generation=Path(job["generation"]["path"]), generation_sha256=job["generation"]["sha256"], observations=Path(observations["path"]), observations_sha256=observations["sha256"])
            value = code.compare(comparison_args, locked, bound)
            report["comparison"] = write_new(output / "Comparison.json", value)
            report["passed"] = value["sheet_lifecycle_passed"] and all(row["passed"] for row in statuses) and len(statuses) == 12 and "pipeline_error_type" not in report and "trailing_control_error_type" not in report
        except Exception as error:
            report["comparison_error_type"] = type(error).__name__
        write_new(output / "Result.json", report)
    return report


def prepare(args):
    tools = Path(__file__).resolve().parent
    manifest = load({"path": str(tools.parent / "Tools.json"), "sha256": args.tools_sha256})
    require(set(manifest["tools_sha256"]) == set(TOOLS), "frozen tool inventory differs")
    for name, expected in manifest["tools_sha256"].items():
        require(fingerprint(tools / name) == expected, "frozen preparation source changed")
    for value in (args.tools_sha256, args.binding_sha256, args.generation_sha256):
        require(re.fullmatch(r"[0-9a-f]{64}", value) is not None, "exact metadata hashes required")
    require(all(PureWindowsPath(value).is_absolute() for value in (args.binding, args.generation, args.guest_control, args.guest_output)), "absolute guest metadata, control and output paths required")
    guest = PureWindowsPath(args.guest_root)
    require(guest.is_absolute() and PureWindowsPath(args.guest_python).is_absolute(), "absolute guest packet and Python paths required")
    root = args.output.resolve()
    root.mkdir(parents=True, exist_ok=False)
    (root / "Tools").mkdir()
    for name in TOOLS:
        shutil.copyfile(tools / name, root / "Tools" / name)
    shutil.copyfile(tools.parent / "Tools.json", root / "Tools.json")
    job = {"schema": "kit.sw2026.blank-drawing-native-job.v1", "tools": {"path": str(guest / "Tools.json"), "sha256": args.tools_sha256}, "binding": {"path": args.binding, "sha256": args.binding_sha256}, "generation": {"path": args.generation, "sha256": args.generation_sha256}, "guest_python": args.guest_python, "output_root": args.guest_output, "source_root": SOURCE_ROOT, "control": {"path": args.guest_control, "sha256": "227f12b5834f73e31d1cb64db9e615418852bfba6c30d6c2700be6e26cc4932b"}, "phase_timeout_seconds": 300, "phase_order": [base + "/" + stage for base in BASES for stage in STAGES]}
    written = write_new(root / "Job.json", job)
    command = [args.guest_python, "-B", str(guest / "Tools" / "RunBlankDrawingComparison01.py")]
    tail = ["--job", str(guest / "Job.json"), "--job-sha256", written["sha256"]]
    recipe = {"schema": "kit.sw2026.blank-drawing-native-recipe.v1", "job_sha256": written["sha256"], "commands": [{"name": mode, "argv": command + [mode] + tail} for mode in ("verify", "run")], "guest_only_native_execution": True, "root_only_VM_owner": True, "private_values_on_stdout": False, "source_path_arrays": {slot: [str(PureWindowsPath(SOURCE_ROOT) / slot / "Native" / "Source.SLDDRW"), str(PureWindowsPath(SOURCE_ROOT) / slot / "edit" / "EditedDrawing.SLDDRW")] for slot in ("Slot01", "Slot02")}}
    receipt = write_new(root / "Recipe.json", recipe)
    return {"passed": True, "job_sha256": written["sha256"], "recipe_sha256": receipt["sha256"], "native_source_reads": 0, "native_launches": 0}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "verify", "run", "worker"))
    parser.add_argument("--job", type=Path)
    parser.add_argument("--job-sha256")
    parser.add_argument("--phase", choices=tuple(base + "/" + stage for base in BASES for stage in STAGES))
    parser.add_argument("--gate", type=Path)
    parser.add_argument("--gate-sha256")
    parser.add_argument("--prior-sha256")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--tools-sha256")
    parser.add_argument("--guest-root")
    parser.add_argument("--guest-python")
    parser.add_argument("--guest-output")
    parser.add_argument("--guest-control")
    parser.add_argument("--binding")
    parser.add_argument("--binding-sha256")
    parser.add_argument("--generation")
    parser.add_argument("--generation-sha256")
    args = parser.parse_args()
    value = None
    try:
        if args.mode == "prepare":
            value = prepare(args)
        elif args.mode == "worker":
            value = worker(args)
        elif args.mode == "run":
            value = run(args)
        else:
            code, job, bound, locked = verify_job(args.job, args.job_sha256)
            generation_gate(code, job, bound, locked, True)
            value = {"passed": True, "native_source_reads": 0, "native_launches": 0}
    except Exception as error:
        value = {"passed": False, "error_type": type(error).__name__}
    if args.mode == "worker":
        value.setdefault("name", args.phase)
        job = load({"path": str(args.job), "sha256": args.job_sha256})
        path = Path(job["output_root"]) / "Workers" / (args.phase.replace("/", "_") + ".json")
        write_new(path, value)
    print(json.dumps({"passed": value["passed"], "mode": args.mode, "error_type": value.get("error_type"), "private_values_printed": False}))
    return 0 if value["passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
