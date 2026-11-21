import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from uuid import uuid4

import BlankDrawingComparison01 as comparison

SCHEMA = "kit.sw2026.blank-drawing-source-closure.v1"
SOURCE_ROOT = Path(r"C:\KitBlankDrawingSource121")
BUILD_ROUTES = ("extension", "solidworks.slddrw")


def descriptor(path):
    return {"path": str(path), "sha256": sha256(path.read_bytes()).hexdigest()}


def freeze(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, indent=2, allow_nan=False) + "\n")
    return descriptor(path)


def verify_closure(root, manifest):
    comparison.require(manifest["schema"] == SCHEMA, "wrong writer source manifest")
    files = manifest["files"]
    comparison.require(len(files) > 0 and len(files) == manifest["file_count"], "incomplete closure")
    for name, digest in files.items():
        path = Path(name)
        comparison.require(not path.is_absolute() and ".." not in path.parts, "invalid writer manifest path")
        actual = root / path
        if actual.is_symlink() or descriptor(actual)["sha256"] != digest:
            raise ValueError("writer source differs from its manifest")


def bind(args):
    packet = args.packet
    local = args.private
    comparison.require(packet.is_absolute() and local.is_absolute() and local.drive.upper() == "C:", "invalid evaluation paths")
    comparison.require(not local.exists() and not local.is_relative_to(SOURCE_ROOT), "use a fresh separate private directory")
    manifest = comparison.load({"path": str(packet / "WriterManifest.json"), "sha256": args.manifest_sha256})
    verify_closure(packet, manifest)
    for filename in ("SourceLock.json", "ExplicitOptions.json", "NativeTools.json"):
        comparison.pinned({"path": str(packet / filename), "sha256": manifest["inputs"][filename]})

    local.mkdir()
    for name in manifest["files"]:
        target = local / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(packet / name, target)
    for name in ("WriterManifest.json", "SourceLock.json", "ExplicitOptions.json", "NativeTools.json"):
        shutil.copyfile(packet / name, local / name)
    verify_closure(local, manifest)
    writer_manifest = descriptor(local / "WriterManifest.json")
    comparison.require(writer_manifest["sha256"] == args.manifest_sha256, "private manifest copy changed")
    verified = freeze(local / "WriterVerification.json", {
        "schema": "kit.sw2026.blank-drawing-writer-verification.v1",
        "passed": True,
        "all_manifest_entries_verified": True,
        "verified_entries": manifest["file_count"],
        "writer_manifest_sha256": args.manifest_sha256,
        "python_version": sys.version.split()[0],
    })
    return freeze(local / "MethodBinding.json", {
        "schema": "kit.sw2026.blank-drawing-method-binding.v1",
        "comparator_sha256": descriptor(local / "Tools/BlankDrawingComparison01.py")["sha256"],
        "source_lock": descriptor(local / "SourceLock.json"),
        "writer_epoch": manifest["writer_epoch"],
        "private_intent_reads_before_binding": 0,
        "native_payload_reads_before_generation": 0,
        "artifacts": {
            "writer_manifest": writer_manifest,
            "writer_verification": verified,
            "neutral_mapper": descriptor(local / "Tools/PublicBlankIntent.py"),
            "explicit_options": descriptor(local / "ExplicitOptions.json"),
            "runtime_guard": descriptor(local / "Tools/BuildPublicBlankDrawing.py"),
            "native_observer_manifest": descriptor(local / "NativeTools.json"),
        },
    })


def private_worker(argv, root, src):
    completed = subprocess.run(
        [sys.executable, "-B", *map(str, argv)], cwd=root,
        env={**os.environ, "PYTHONPATH": str(src), "PYTHONNOUSERSITE": "1"},
        capture_output=True, timeout=120, check=False,
    )
    return completed


def generate(args):
    root = args.private
    bound, locked = comparison.binding(root / "MethodBinding.json", args.binding_sha256)
    manifest = comparison.load(bound["artifacts"]["writer_manifest"])
    verify_closure(root, manifest)
    comparison.require(Path(__file__).resolve() == (root / "Tools" / Path(__file__).name).resolve(), "use the private frozen generation tool")
    tools = root / "Tools"
    src = root / "src"
    states = {}
    for slot in comparison.SLOTS:
        workspace = root / "Generation" / slot
        workspace.mkdir(parents=True)
        intent = SOURCE_ROOT / slot / "Intent.json"
        intent_hash = locked["slots"][slot]["intent_sha256"]
        prediction = workspace / "Prediction.json"
        phase = private_worker([
            tools / "BlankDrawingComparison01.py", "predict",
            "--binding", root / "MethodBinding.json", "--binding-sha256", args.binding_sha256,
            "--slot", slot, "--intent", intent, "--output", prediction,
        ], root, src)
        comparison.require(phase.returncode == 0 and json.loads(phase.stdout)["passed"] is True, "sealed neutral prediction failed")
        original = comparison.load({"path": str(intent), "sha256": intent_hash})
        neutral = freeze(workspace / "Neutral.json", {
            "schema": "kit.sw2026.public-blank-neutral-intent.v1",
            **{name: original[name] for name in ("sheet_id", "sheet_name", "width_m", "height_m", "scale_ratio")},
        })
        block_id = str(uuid4())
        target = workspace / (slot + ".SLDDRW")
        rows = []
        for route in BUILD_ROUTES:
            frozen_dir = workspace / ("ByExtension" if route == "extension" else "ByFormat")
            frozen_dir.mkdir()
            report = frozen_dir / "Build.json"
            result = private_worker([
                tools / "BuildPublicBlankDrawing.py", "--intent", neutral["path"],
                "--intent-sha256", neutral["sha256"],
                "--options", bound["artifacts"]["explicit_options"]["path"],
                "--options-sha256", bound["artifacts"]["explicit_options"]["sha256"],
                "--target", target, "--report", report,
                "--route", route, "--epoch", bound["writer_epoch"], "--block-id", block_id,
                "--writer-manifest-sha256", bound["artifacts"]["writer_manifest"]["sha256"],
            ], root, src)
            if result.returncode != 0:
                (frozen_dir / "Failure.bin").write_bytes(result.stderr)
                raise ValueError("guarded public drawing build failed")
            row = json.loads(report.read_bytes())
            comparison.require(row["output"] == descriptor(target), "guarded output changed")
            frozen = frozen_dir / target.name
            target.rename(frozen)
            row["output"] = descriptor(frozen)
            rows.append(row)
        first, second = (comparison.pinned(row["output"]) for row in rows)
        comparison.require(first == second and first, "two independent public builds differ")
        states[slot] = {"intent_sha256": intent_hash, "prediction": descriptor(prediction), "builds": rows}
    return freeze(root / "GenerationFreeze.json", {
        "schema": "kit.sw2026.blank-drawing-generation-freeze.v1",
        "method_binding_sha256": args.binding_sha256,
        "native_payload_reads": 0,
        "all_outputs_frozen_before_native_attach": True,
        "slots": states,
    })


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("bind", "generate"))
    parser.add_argument("--private", type=Path, required=True)
    parser.add_argument("--packet", type=Path)
    parser.add_argument("--manifest-sha256")
    parser.add_argument("--binding-sha256")
    args = parser.parse_args()
    try:
        comparison.require(os.name == "nt", "private evaluation requires the reserved guest")
        value = bind(args) if args.mode == "bind" else generate(args)
    except Exception as error:
        print(json.dumps({"passed": False, "error_type": type(error).__name__, "native_launches": 0}))
        return 3
    print(json.dumps({"passed": True, "sha256": value["sha256"], "native_launches": 0}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
