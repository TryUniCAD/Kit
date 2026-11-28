from __future__ import annotations

import argparse
from hashlib import sha256
import json
from math import isclose
from pathlib import Path
import subprocess
import sys


def require(value, message):
    if not value:
        raise ValueError(message)


def identity(path):
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": sha256(data).hexdigest()}


def write_json(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def run_worker(python, tool, payload, prefix, report):
    argv = [python, "-I", "-B", str(tool)]
    stdin = json.dumps(payload, sort_keys=True, ensure_ascii=False, allow_nan=False).encode("utf-8")
    prefix.with_suffix(".stdin.json").write_bytes(stdin)
    report["process_attempt_count"] += 1
    result = subprocess.run(argv, input=stdin, capture_output=True, timeout=300)
    prefix.with_suffix(".stdout.json").write_bytes(result.stdout)
    prefix.with_suffix(".stderr.txt").write_bytes(result.stderr)
    checkpoint = {"argv": argv, "exit_code": result.returncode,
                  "stdin": identity(prefix.with_suffix(".stdin.json")),
                  "stdout": identity(prefix.with_suffix(".stdout.json")),
                  "stderr": identity(prefix.with_suffix(".stderr.txt"))}
    write_json(prefix.with_suffix(".Record.json"), checkpoint)
    report["process_count"] += 1
    report["completed_workers"].append(checkpoint)
    require(result.returncode == 0, "guarded reconstruction worker failed: " + prefix.name)
    value = json.loads(result.stdout)
    require(value.get("passed") is True, "guarded reconstruction worker did not pass: " + prefix.name)
    return value, checkpoint


def check_geometry(actual, row):
    geometry, boss = row["geometry"], row["boss"]
    expected = {"sketch_name": geometry["sketch_name"], "feature_name": boss["name"],
                "driver_names": [value["name"] for value in geometry["drivers"]], "depth_name": boss["depth_name"],
                "configuration_name": row["origins"]["configuration"]["name"],
                "name": row["file_identity_domains"]["modeled_name"]}
    require(all(actual["child_neutral"][key] == value for key, value in expected.items()), "reconstructed child parameter feature or configuration identity differs")
    require(len(actual["child_neutral"]["vertices_m"]) == 4, "reconstructed contour membership differs")
    for point, expected_point in zip(actual["child_neutral"]["vertices_m"], geometry["vertices_m"], strict=True):
        require(all(isclose(a, b, rel_tol=1e-12, abs_tol=1e-14) for a, b in zip(point, expected_point, strict=True)), "reconstructed actual child points differ")
    require(isclose(actual["child_neutral"]["depth_m"], boss["depth_m"], rel_tol=1e-12, abs_tol=1e-14), "reconstructed driving depth differs")
    require(actual["child_shape"]["anchor_kind"] == geometry["kind"]
            and actual["child_shape"]["origin_coincidences"] == len(geometry["binary_roles"])
            and actual["child_shape"]["visible_lines"] == geometry["visible_line_count"], "reconstructed anchor or relation membership differs")
    require(actual["native_child_path"] == row["origins"]["resolved_child"]["path"]
            and actual["native_drawing_path"] == row["origins"]["drawing_file"]["path"], "reconstructed native file origins differ")
    sheet, = row["portable_drawing_document"]["sheets"]["$tuple"]
    view, = sheet["views"]["$tuple"]
    require(actual["orientation"] == view["orientation_name"] and actual["view_scale"] == view["scale_ratio"]["$tuple"]
            and actual["view_position_m"] == [view["position"]["x"], view["position"]["y"]], "reconstructed drawing placement differs")


def main():
    parser = argparse.ArgumentParser(description="Reconstruct only complete private portable requests in independent guarded native-format processes")
    parser.add_argument("candidate", type=Path)
    parser.add_argument("normalization", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--normalization-sha256", required=True)
    parser.add_argument("--tools-manifest", type=Path, required=True)
    parser.add_argument("--tools-manifest-sha256", required=True)
    args = parser.parse_args()
    require(not args.output.exists(), "portable reconstruction output must be unused")
    require(identity(args.tools_manifest)["sha256"] == args.tools_manifest_sha256, "portable normalization method custody differs")
    tools = json.loads(args.tools_manifest.read_bytes())
    require(tools["source_manifest_sha256"] == args.manifest_sha256, "portable method has another writer closure")
    verify_path = args.tools_manifest.parent / "Tools/InspectOriginPortable.py"
    expected, = [row for row in tools["files"] if row["path"] == verify_path.name]
    require(identity(verify_path)["sha256"] == expected["sha256"], "source verifier differs from the frozen method")
    sys.path.append(str(verify_path.parent))
    from InspectOriginPortable import verify_source
    source_manifest = verify_source(args.candidate, args.manifest_sha256)
    result_path = args.normalization / "Result.json"
    require(identity(result_path)["sha256"] == args.normalization_sha256, "portable normalized source observation changed")
    normalized = json.loads(result_path.read_bytes())
    require(normalized["schema"] == "kit.sw2026.origin-portable-normalization.v1" and normalized["source_manifest_sha256"] == args.manifest_sha256
            and normalized["tool_manifest_sha256"] == args.tools_manifest_sha256 and normalized["data_collected"] is True,
            "portable normalization result belongs to another source or method")
    admitted = [row for row in normalized["cases"] if row["request_complete"]]
    require(len(admitted) == normalized["request_count"] == 4 and all(row["role"] == "generated-replay06" for row in admitted),
            "this disclosed reconstruction profile requires exactly its four generated requests; original source refusals remain separate")
    args.output.mkdir(parents=True, exist_ok=False)
    report = {"schema": "kit.sw2026.origin-portable-reconstruction.v1", "passed": False,
              "normalization": identity(result_path), "source_manifest_sha256": args.manifest_sha256,
              "source_file_count": source_manifest["file_count"], "tools_manifest": identity(args.tools_manifest),
              "controller": identity(Path(__file__).resolve()), "cases": [], "process_count": 0, "process_attempt_count": 0,
              "process_count_scope": "completed worker invocations with captured process status", "completed_workers": [],
              "original_source_conversion_qualified": False, "public_strict_drawing_reader_changed": False,
              "writer_changed": False, "native_acceptance": False, "heldout_acceptance": False, "hidden_inputs_read": 0}
    code = args.candidate / "CodeRoot/re/tooling/sw2026"
    try:
        for index, row in enumerate(admitted):
            request_path = args.normalization / row["request_file"]["path"]
            require(request_path.resolve().parent == args.normalization.resolve() and not request_path.is_symlink(), "portable request escaped the immutable normalization output")
            require(identity(request_path)["sha256"] == row["request_file"]["sha256"] and request_path.stat().st_size == row["request_file"]["bytes"], "portable request custody differs")
            request = json.loads(request_path.read_bytes())
            require(row["constructor_admitted"] is True and not row["known_constructor_boundaries"] and request == row["request"], "portable request is not fully admitted by its private method")
            record = {"case": row["case"], "request": identity(request_path), "passed": False, "workers": []}
            report["cases"].append(record)
            builds = []
            for repeat in range(2):
                built, worker = run_worker(sys.executable, code / "OriginPairProcess.py", request, args.output / (str(index) + "Build" + str(repeat)), report)
                record["workers"].append(worker)
                require(built["runtime_input_file_access_attempts"] == 0 and not built["sdk_research_imports"]
                        and built["complete_typed_roundtrip"] is True and built["child_graph_and_bytes_unchanged"] is True, "portable construction crossed its no-input-read or typed-graph boundary")
                check_geometry(built, row);builds.append(built)
            require(builds[0] == builds[1], "portable source reconstruction is not deterministic")
            prepared, worker = run_worker(sys.executable, code / "OriginPairPrepare.py", builds[0], args.output / (str(index) + "Prepare"), report)
            record["workers"].append(worker)
            require(prepared["complete_definition_byte_identity"] is True and prepared["typed_linked_child_complete"] is True
                    and prepared["profile"] == builds[0]["profile"] and prepared["child_shape"] == builds[0]["child_shape"], "separate portable child profile or definition preparation differs")
            record.update(passed=True, deterministic_bytes=True, complete_typed_preparation=True,
                          drawing_sha256=builds[0]["drawing_sha256"], child_sha256=builds[0]["child_sha256"],
                          actual_model_geometry_and_driver_identity=True, zero_runtime_input_reads=True)
        verify_source(args.candidate, args.manifest_sha256)
        require(identity(result_path)["sha256"] == args.normalization_sha256, "normalization input changed during reconstruction")
        report["passed"] = True
    except Exception as error:
        report.update(exception=type(error).__name__, diagnostic=str(error))
    write_json(args.output / "Result.json", report)
    print(json.dumps({key: report[key] for key in ("passed", "process_count", "original_source_conversion_qualified", "native_acceptance")}))
    return 0 if report["passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
