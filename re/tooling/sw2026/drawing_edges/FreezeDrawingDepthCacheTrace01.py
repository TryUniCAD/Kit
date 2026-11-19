from __future__ import annotations

import argparse
import ast
from hashlib import sha256
import json
from pathlib import Path, PureWindowsPath
import shutil

BASE_TRIAL = "2c2ac4aa9a09a170c9667abc8d81d6cf5c25a4f6192cf436ef7380f14869adf7"
BASE_FILES = "52d0fa5ec22dea33cc296e42d97ca47992a452af3b403b878b3a481ad7da033c"
BASE_RESULT = "92f51a9a5c5e7c7136b01d7a56d73c840e1a5e81df8f7af4a612ca36aa644401"
ORIGINAL_TRIAL = "36143744fc79f19fb60434d24884288f72733e764ed9fd8a8138aff4233d0872"
PACKAGE = "875678516f9ceed4a1c8b9b106d165106fcaa38723ad7c584c47b95b231600de"
SOURCES = {
    "DrawingEdgeCacheTrace01.py": "bc41c15f5de299732c271facc40aa7d18ae0111cc8054a16df84fa74987260c7",
    "DrawingSaveAggregateDbgEng.py": "d312a5b604d40ca3c5bccac65c35ce186aea5311bc21949939aa965fa3720c3f",
    "DrawingSavePreviewGateDbgEng.py": "53dc45e2ec6628b9518d3a31aa9ea50ed1c6add2156a68fb61f92aedd798906c",
    "DrawingSavePropertiesGateDbgEng.py": "9a42ce005817effb3aa28c1d3f1fad98d7a18aa0ebaf783bfca560586863cf04",
    "ObserveDrawingEdgeCache01.py": "920e889e557e32071726842725a00d45dee896abe0deed6bc329e6320e62ab2e",
    "RunDrawingEdgeCacheTrace01.py": "b5ee3f713ddab5f0e9899c6e1b8ac719dc176ec53d8f7489cd0a09b4a9616011",
}
PHASES = {
    name + phase
    for name in ("ControlBefore", "Generated", "ControlAfter")
    for phase in ("OpenEditSave", "FreshReopen")
}


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


def baseline_files(packet, baseline):
    require(digest(packet / "Trial.json") == BASE_TRIAL, "depth baseline trial differs")
    require(
        digest(packet / "Files.json") == BASE_FILES,
        "depth baseline file manifest differs",
    )
    require(digest(baseline) == BASE_RESULT, "terminal depth baseline receipt differs")
    result = json.loads(baseline.read_bytes())
    require(
        result.get("passed") is True
        and result.get("packet_sha256") == BASE_TRIAL
        and result.get("controls_healthy") is True
        and result.get("distinct_processes") == 6
        and result.get("inputs_unchanged") is True
        and result.get("encoded_slots_unchanged") is True
        and result.get("heldout_inputs_read") == 0
        and set(result.get("phases") or {}) == PHASES,
        "the exact terminal six-process depth baseline must pass first",
    )
    identities = []
    for name, row in result["phases"].items():
        require(
            row.get("passed") is True
            and row.get("open_errors") == row.get("open_warnings") == 0
            and row.get("worker_exit_code") == 0
            and row.get("worker_timed_out") is False,
            "an actual depth baseline phase did not pass: " + name,
        )
        identities.append(row["oracle_identity"]["process_creation_filetime"])
        if name.endswith("OpenEditSave"):
            require(
                row.get("save_status") == [True, 0, 0], "baseline save status differs"
            )
    require(
        None not in identities and len(set(identities)) == 6,
        "baseline processes are not independent",
    )
    files = json.loads((packet / "Files.json").read_bytes())
    require(len(files) == 23, "the complete depth baseline source closure is required")
    for name, row in files.items():
        path = (packet / name).resolve(strict=True)
        require(
            path.is_relative_to(packet)
            and path.is_file()
            and path.stat().st_size == row["bytes"]
            and digest(path) == row["sha256"],
            "frozen depth baseline file differs: " + name,
        )
    return files


def trace_sources(directory):
    sources = {}
    for name, expected in SOURCES.items():
        path = directory / name
        require(
            path.is_file() and digest(path) == expected,
            "original two-stop source differs: " + name,
        )
        raw = path.read_bytes()
        compile(ast.parse(raw), str(path), "exec")
        sources[name] = raw
    runner = "RunDrawingEdgeCacheTrace01.py"
    old = ("BASE_TRIAL = '" + ORIGINAL_TRIAL + "'").encode()
    new = ("BASE_TRIAL = '" + BASE_TRIAL + "'").encode()
    require(sources[runner].count(old) == 1, "original runner binding is not unique")
    sources[runner] = sources[runner].replace(old, new)
    compile(ast.parse(sources[runner]), runner, "exec")
    return sources


def verify_engine(directory, source):
    metadata = json.loads((directory / "DbgEngPackage.json").read_bytes())
    require(metadata["sha256"] == PACKAGE, "cached debugger package metadata differs")
    package = directory / "Microsoft.Debugging.Platform.DbgEng.20260319.1511.0.nupkg"
    require(digest(package) == PACKAGE, "cached debugger package bytes differ")
    tree = ast.parse(source)
    assignment = next(
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "ENGINE_SHA256"
            for target in node.targets
        )
    )
    engines = ast.literal_eval(assignment.value)
    require(len(engines) == 5, "the complete original AMD64 engine closure is required")
    for name, expected in engines.items():
        require(
            digest(directory / "DbgEng/content/amd64" / name) == expected,
            "cached debugger image differs: " + name,
        )
    return engines


def freeze(args):
    packet = args.source_packet.resolve(strict=True)
    baseline = args.baseline.resolve(strict=True)
    output = args.output.resolve()
    require(not output.exists(), "use an unused trace packet directory")
    guest = PureWindowsPath(args.guest_packet)
    interpreter = PureWindowsPath(args.guest_python)
    debugger = PureWindowsPath(args.debugger_guest_directory)
    require(
        guest.is_absolute() and interpreter.is_absolute() and debugger.is_absolute(),
        "all guest identities must be explicit absolute Windows paths",
    )
    files = baseline_files(packet, baseline)
    sources = trace_sources(args.trace_sources.resolve(strict=True))
    engines = verify_engine(
        args.debugger_root.resolve(strict=True), sources["ObserveDrawingEdgeCache01.py"]
    )
    output.mkdir()
    for name in [*files, "Files.json"]:
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(packet / name, target)
    shutil.copyfile(baseline, output / "RequiredBaseline.json")
    tools = output / "TraceTools"
    tools.mkdir()
    for name, raw in sources.items():
        (tools / name).write_bytes(raw)
    job = {
        "schema": "kit.sw2026.drawing-edge-cache-two-stop.v1",
        "base_trial_sha256": BASE_TRIAL,
        "base_files_sha256": BASE_FILES,
        "required_baseline_sha256": BASE_RESULT,
        "heldout_inputs_read": 0,
        "native_acceptance": False,
        "debugger_directory": str(debugger),
        "debugger_package_sha256": PACKAGE,
        "debugger_files_sha256": engines,
        "trace_tools_sha256": {name: digest(tools / name) for name in sorted(sources)},
        "original_trace_sources_sha256": SOURCES,
        "adaptation": {
            "freezer_sha256": digest(Path(__file__)),
            "runner_only_change": "BASE_TRIAL binding to exact passed attached-cap-note-depth-07 lifecycle",
            "base_lifecycle_files_unchanged": True,
            "source_sites_engine_and_cleanup_unchanged": True,
        },
        "sites": [
            {
                "module": "slduiu.dll",
                "rva": 0x13AAED7,
                "sample": "actual component nonnull, requested downstream ID u32, kernel edge nonnull",
            },
            {
                "module": "slduiu.dll",
                "rva": 0x13AAEDC,
                "sample": "same thread/stack; returned reference nonnull",
            },
        ],
        "selected_annotation_edge_joined_to_sampled_id": False,
        "generated_downstream_writer_qualified": False,
        "generated_owner_id_discriminator_enabled": False,
    }
    trial = output / "TraceTrial.json"
    write_json(trial, job)
    trial_sha = digest(trial)
    script = str(guest / "TraceTools/RunDrawingEdgeCacheTrace01.py")
    native_trial = str(guest / "TraceTrial.json")
    prefix = [
        "prlctl",
        "exec",
        "Windows 11",
        "--current-user",
        str(interpreter),
        "-B",
        script,
    ]
    recipe = {
        "schema": "kit.sw2026.drawing-depth-cache-trace.recipe.v1",
        "packet_sha256": trial_sha,
        "required_baseline_sha256": BASE_RESULT,
        "source_commit_before_native_required": True,
        "verify_argv": prefix + ["verify", native_trial, "--sha256", trial_sha],
        "run_argv": prefix + ["run", native_trial, "--sha256", trial_sha],
        "progress_result": str(guest / "Inspection/Result.json"),
        "scope": "first matched cache lookup is unjoined to the selected annotation edge",
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
    write_json(output / "TraceFiles.json", frozen)
    return {
        "trial": str(trial),
        "trial_sha256": trial_sha,
        "files_sha256": digest(output / "TraceFiles.json"),
        "recipe_sha256": digest(output / "Recipe.json"),
        "copied_baseline_files": len(files) + 1,
        "trace_modules": len(sources),
        "cad_processes_started": 0,
        "native_acceptance": False,
    }


def main():
    parser = argparse.ArgumentParser()
    for name in (
        "source-packet",
        "baseline",
        "trace-sources",
        "debugger-root",
        "output",
    ):
        parser.add_argument("--" + name, type=Path, required=True)
    for name in ("guest-packet", "guest-python", "debugger-guest-directory"):
        parser.add_argument("--" + name, required=True)
    print(json.dumps(freeze(parser.parse_args()), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
