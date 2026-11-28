from __future__ import annotations

import argparse
import ast
from hashlib import sha256
import json
from pathlib import Path, PureWindowsPath
import shutil

from FreezeDrawingDepthCacheTrace01 import baseline_files, trace_sources, verify_engine

BASE_TRIAL = "2c2ac4aa9a09a170c9667abc8d81d6cf5c25a4f6192cf436ef7380f14869adf7"
BASE_RESULT = "92f51a9a5c5e7c7136b01d7a56d73c840e1a5e81df8f7af4a612ca36aa644401"
FAILED_TRACE = "040e859f432f6b0b3999a0e65b74706a4f7d5d9d385fe43a0f17e4196289c468"
FREEZER_DEPENDENCY = "4cb88edb6f6f08f29fab73671c3c8401a4bfafcad381e784cdc53275851b23a7"


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as output:
        output.write(
            json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n"
        )


def prepare(args):
    packet = args.source_packet.resolve(strict=True)
    baseline = args.baseline.resolve(strict=True)
    failed = args.failed_trace.resolve(strict=True)
    output = args.output.resolve()
    require(not output.exists(), "use an unused preparation-probe directory")
    require(
        digest(Path(baseline_files.__code__.co_filename)) == FREEZER_DEPENDENCY,
        "the shared baseline freezer dependency changed",
    )
    files = baseline_files(packet, baseline)
    require(digest(failed) == FAILED_TRACE, "the actual failed two-stop trace differs")
    negative = json.loads(failed.read_bytes())
    require(
        negative["passed"] is False
        and len(negative["phases"]) == 2
        and all(
            row["annotation_geometry_lifecycle_passed"]
            and row["cache_source_evaluation"]["route"] == "call_unobserved"
            and row["cache_source_evaluation"]["observer_completed_cleanly"]
            for row in negative["phases"].values()
        ),
        "the distinct clean-save/unobserved-call evidence is required",
    )
    sources = trace_sources(args.trace_sources.resolve(strict=True))
    sources.pop("RunDrawingEdgeCacheTrace01.py")
    engines = verify_engine(
        args.debugger_root.resolve(strict=True), sources["ObserveDrawingEdgeCache01.py"]
    )
    for name in ("DrawingPreparationGateTrace01.py", "RunDrawingPreparationGate01.py"):
        raw = (args.new_tools / name).read_bytes()
        compile(ast.parse(raw), name, "exec")
        sources[name] = raw
    rules = json.loads(args.rules.read_bytes())
    binding = json.loads(args.binding.read_bytes())
    require(
        rules["stop"]["preferred_va"] == "0x3df07bce"
        and rules["stop"]["rva"] == 0x347BCE
        and rules["original_source_identity_verified"] is True,
        "the fixed source-backed decision differs",
    )
    require(
        binding["drawing_sha256"]
        == json.loads((packet / "Trial.json").read_bytes())["cases"][0][
            "drawing_sha256"
        ]
        and binding["model_view_class"] == "moAbsoluteView"
        and type(binding["native_view_id"]) is int
        and binding["native_view_id"] > 0,
        "the disclosed source model view differs",
    )
    guest, interpreter, debugger = (
        PureWindowsPath(value)
        for value in (
            args.guest_packet,
            args.guest_python,
            args.debugger_guest_directory,
        )
    )
    require(
        all(value.is_absolute() for value in (guest, interpreter, debugger)),
        "all guest identities must be explicit absolute Windows paths",
    )
    output.mkdir()
    for name in [*files, "Files.json"]:
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(packet / name, target)
    for source, name in (
        (baseline, "PassedBaseline.json"),
        (failed, "UnobservedTrace.json"),
        (args.rules, "SourceRules.json"),
        (args.binding, "SourceViewBinding.json"),
    ):
        shutil.copyfile(source, output / name)
    tools = output / "ProbeTools"
    tools.mkdir()
    for name, raw in sources.items():
        (tools / name).write_bytes(raw)
    config = {
        "schema": "kit.sw2026.drawing-preparation-gate.v1",
        "base_trial_sha256": BASE_TRIAL,
        "required_baseline_sha256": BASE_RESULT,
        "required_failed_trace_sha256": FAILED_TRACE,
        "source_rules_sha256": digest(args.rules),
        "source_view_binding_sha256": digest(args.binding),
        "model_view_native_id": binding["native_view_id"],
        "module_sha256": "61c8481374431866f97416ce5109329f9c38e7e85b56a9f95d41bdf3122cdc47",
        "rva": 0x347BCE,
        "debugger_directory": str(debugger),
        "debugger_files_sha256": engines,
        "probe_tools_sha256": {name: digest(tools / name) for name in sorted(sources)},
        "freezer_sha256": digest(Path(__file__)),
        "freezer_dependency_sha256": FREEZER_DEPENDENCY,
        "roles": ["ControlBefore", "PreparationProbe", "ControlAfter"],
        "scope": "ordinary disclosed control plus one selected-view read-only preparation decision; no generated native phase or child-cache lookup claim",
        "unobserved_is_a_distinct_diagnostic_outcome": True,
        "native_acceptance": False,
        "heldout_inputs_read": 0,
        "generated_native_inputs_run": 0,
    }
    write_json(output / "ProbeTrial.json", config)
    trial_sha = digest(output / "ProbeTrial.json")
    prefix = [
        "prlctl",
        "exec",
        "Windows 11",
        "--current-user",
        str(interpreter),
        "-B",
        str(guest / "ProbeTools/RunDrawingPreparationGate01.py"),
    ]
    recipe = {
        "schema": "kit.sw2026.drawing-preparation-gate-recipe.v1",
        "packet_sha256": trial_sha,
        "verify_argv": prefix
        + ["verify", str(guest / "ProbeTrial.json"), "--sha256", trial_sha],
        "run_argv": prefix
        + ["run", str(guest / "ProbeTrial.json"), "--sha256", trial_sha],
        "progress_result": str(guest / "Inspection/Result.json"),
        "source_commit_before_native_required": True,
        "diagnostic_completed_does_not_mean_gate_observed": True,
        "native_acceptance": False,
    }
    write_json(output / "Recipe.json", recipe)
    frozen = {
        path.relative_to(output).as_posix(): {
            "bytes": path.stat().st_size,
            "sha256": digest(path),
        }
        for path in sorted(output.rglob("*"))
        if path.is_file()
    }
    write_json(output / "ProbeFiles.json", frozen)
    return {
        "trial_sha256": trial_sha,
        "recipe_sha256": digest(output / "Recipe.json"),
        "files_sha256": digest(output / "ProbeFiles.json"),
        "native_processes_started": 0,
    }


def main():
    parser = argparse.ArgumentParser()
    for name in (
        "source-packet",
        "baseline",
        "failed-trace",
        "trace-sources",
        "debugger-root",
        "new-tools",
        "rules",
        "binding",
        "output",
    ):
        parser.add_argument("--" + name, type=Path, required=True)
    for name in ("guest-packet", "guest-python", "debugger-guest-directory"):
        parser.add_argument("--" + name, required=True)
    print(json.dumps(prepare(parser.parse_args()), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
