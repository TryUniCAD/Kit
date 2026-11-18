from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n")
    return digest(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--native-inputs", type=Path)
    arguments = parser.parse_args()
    root, output = arguments.root.resolve(), arguments.output.resolve()
    manifest = json.loads(arguments.source_manifest.read_bytes())
    if len(manifest["files_sha256"]) != manifest["file_count"]:
        raise ValueError("source manifest count disagrees")
    for relative, expected in manifest["files_sha256"].items():
        path = (root / relative).resolve()
        if not path.is_relative_to(root) or digest(path) != expected:
            raise ValueError("source custody mismatch: " + relative)
    output.mkdir(parents=True, exist_ok=False)
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join((str(root / "src"), str(root)))
    cases = (
        ("Origin.OriginReadTests", "TestOriginRead", 6, 12),
        ("Origin.OriginScopeTests", "TestOriginScope", 2, 15),
        ("LineDimensions.RectDriveReadTests", "TestRectDrivers", 6, 9),
        ("LineDimensions.RectDriveScopeTests", "TestRectScope", 2, 7),
        ("Lines.LineReadTests", "TestLineRead", 6, 3),
        ("Lines.LineIdentityTests", "TestLineIds", 2, 2),
        ("Lines.LineScopeTests", "TestLineScope", 2, 6),
    )
    code = """import importlib,json,pathlib,sys
root=pathlib.Path(sys.argv[1]).resolve()
sys.path[:0]=[str(root/'src'),str(root)]
target=pathlib.Path(sys.argv[2]);target.mkdir()
getattr(importlib.import_module(sys.argv[3]),sys.argv[4])(target)
modules=[m for n,m in sys.modules.items() if n=='convert' or n.startswith('convert.') or n=='interchange' or n.startswith('interchange.')]
assert modules and all(pathlib.Path(m.__file__).resolve().is_relative_to(root/'src') for m in modules if getattr(m,'__file__',None))
print(json.dumps({'passed':True,'sdk_source_within_root':True,'sdk_modules':len(modules)}))
"""
    results = []
    for suffix, method, builds, reads in cases:
        module = "tests.Convert.Solidworks.Research.Resolved." + suffix
        label = suffix.split(".")[-1]
        started = time.monotonic()
        result = subprocess.run(
            (sys.executable, "-I", "-B", "-c", code, str(root), str(output / label), module, method),
            cwd=root, env=environment, capture_output=True, text=True, timeout=240, check=False)
        (output / (label + ".stdout")).write_text(result.stdout)
        (output / (label + ".stderr")).write_text(result.stderr)
        row = {"module": module, "method": method, "passed": result.returncode == 0,
               "returncode": result.returncode, "seconds": round(time.monotonic() - started, 3),
               "guarded_build_processes_in_recipe": builds, "public_read_processes_in_recipe": reads,
               "stdout_sha256": digest(output / (label + ".stdout")),
               "stderr_sha256": digest(output / (label + ".stderr"))}
        results.append(row)
        print(json.dumps(row, sort_keys=True), flush=True)
    sys.path[:0] = [str(root / "src"), str(root)]
    from interchange import CadDocument
    from tests.Convert.Solidworks.Research.Resolved.Lines.AssertLineBox import AssertLineBox
    from tests.Convert.Solidworks.Research.Resolved.Origin.AssertOrigin import AssertOrigin

    native_results = []
    native_code = """import pathlib,sys
root=pathlib.Path(sys.argv[1]).resolve();sys.path[:0]=[str(root/'src'),str(root)]
from convert import open_document
document=open_document(pathlib.Path(sys.argv[2]),include_brep=False,include_tessellation=False)
modules=[m for n,m in sys.modules.items() if n=='convert' or n.startswith('convert.') or n=='interchange' or n.startswith('interchange.')]
assert modules and all(pathlib.Path(m.__file__).resolve().is_relative_to(root/'src') for m in modules if getattr(m,'__file__',None))
print(document.to_json(indent=None))
"""
    if arguments.native_inputs is not None:
        inputs = json.loads(arguments.native_inputs.read_bytes())
        for item in inputs["files"]:
            path = Path(item["path"])
            if digest(path) != item["sha256"]:
                raise ValueError("input custody mismatch: " + item["label"])
            result = subprocess.run((sys.executable, "-I", "-B", "-c", native_code, str(root), str(path)),
                                    cwd=root, env=environment, capture_output=True, text=True, timeout=90, check=False)
            if result.returncode:
                raise ValueError(item["label"] + " public read failed: " + result.stderr)
            document = CadDocument.from_json(result.stdout)
            length, width, depth = item["dimensions_mm"]
            AssertOrigin(document, length, width)
            AssertLineBox(document, ((0.0, 0.0), (length, 0.0), (length, width), (0.0, width)), depth)
            if digest(path) != item["sha256"]:
                raise ValueError("input changed during public reading")
            sketch, = document.sketches
            row = {"label": item["label"], "file_sha256": item["sha256"], "dimensions_mm": item["dimensions_mm"],
                   "passed": True, "input_immutable": True, "document_sha256": sha256(result.stdout.encode()).hexdigest(),
                   "line_permanent_ids": [entity.attributes["native_line_permanent_id"] for entity in sketch.entities if "native_line_permanent_id" in entity.attributes],
                   "entities": len(sketch.entities), "relations": len(sketch.constraints),
                   "retired_line_rows": len(sketch.attributes.get("native_retired_line_rows", ())),
                   "regions": len(sketch.attributes.get("native_line_regions", ())),
                   "typed_origin_coincidence": sketch.attributes["typed_origin_coincidence"]}
            native_results.append(row)
            write(output / (item["label"] + ".json"), row)
            print(json.dumps(row, sort_keys=True), flush=True)
    for relative, expected in manifest["files_sha256"].items():
        if digest(root / relative) != expected:
            raise ValueError("source changed during replay: " + relative)
    report = {"schema": "kit.sw2026.sdk-origin-read-process-replay.v1", "passed": all(row["passed"] for row in results),
              "source_manifest_sha256": digest(arguments.source_manifest), "source_paths": manifest["file_count"],
              "integration_cohorts": results, "native_reads": native_results,
              "native_inputs_manifest_sha256": None if arguments.native_inputs is None else digest(arguments.native_inputs),
              "sealed_inputs_read": 0, "native_vm_execution": False, "public_writer_qualified": False,
              "fcstd_conversion_accepted": False}
    report_sha = write(output / "Result.json", report)
    print(json.dumps({"passed": report["passed"], "result": str(output / "Result.json"), "sha256": report_sha}, sort_keys=True))
    if not report["passed"]:
        raise SystemExit(3)


if __name__ == "__main__":
    main()
