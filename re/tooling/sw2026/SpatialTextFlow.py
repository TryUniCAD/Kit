from __future__ import annotations

import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parents[2]
sys.path[:] = [value for value in sys.path if Path(value or ".").resolve() != TOOLS]
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]
sys.path.append(str(TOOLS))

import argparse
from base64 import b64decode
from copy import deepcopy
from hashlib import sha256
import json
import subprocess

from OriginPairInput import make_job


def digest(data):
    return sha256(data).hexdigest()


def write_json(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, sort_keys=True, allow_nan=False)
        stream.write("\n")


def verify_source(candidate, expected):
    manifest_path = candidate / "SourceManifest.json"
    if manifest_path.is_symlink() or digest(manifest_path.read_bytes()) != expected:
        raise ValueError("spatial text source manifest custody differs")
    manifest = json.loads(manifest_path.read_bytes())
    if manifest["schema"] != "kit.sw2026.spatial-text-source-closure.v1" or ROOT.resolve() != (candidate / "CodeRoot").resolve():
        raise ValueError("spatial text flow must run from its frozen source closure")
    seen = set()
    for row in manifest["files"]:
        path = Path(row["path"])
        source = ROOT / path
        if (path.is_absolute() or ".." in path.parts or source.is_symlink() or row["path"] in seen
                or not source.resolve(strict=True).is_relative_to(ROOT.resolve())):
            raise ValueError("spatial text frozen source path differs")
        raw = source.read_bytes()
        if len(raw) != row["bytes"] or digest(raw) != row["sha256"]:
            raise ValueError("spatial text source changed: " + row["path"])
        seen.add(row["path"])
    if len(seen) != manifest["file_count"]:
        raise ValueError("spatial text source count differs")
    return manifest


def worker(name, request, prefix):
    encoded = json.dumps(request, sort_keys=True, ensure_ascii=False, allow_nan=False).encode("utf-8")
    prefix.with_suffix(".Request.json").write_bytes(encoded)
    result = subprocess.run([sys.executable, "-I", "-B", str(TOOLS / name)], input=encoded,
                            capture_output=True, cwd=ROOT, timeout=180)
    prefix.with_suffix(".stdout.json").write_bytes(result.stdout)
    prefix.with_suffix(".stderr.txt").write_bytes(result.stderr)
    metadata = {"return_code": result.returncode, "request_sha256": digest(encoded),
                "stdout_sha256": digest(result.stdout), "stderr_sha256": digest(result.stderr),
                "worker_sha256": digest((TOOLS / name).read_bytes())}
    try:
        output = json.loads(result.stdout)
    except (ValueError, UnicodeError):
        output = {"passed": False, "diagnostic": "spatial text worker returned no JSON"}
    return metadata, output


def negative_requests(request):
    for label, value in (("short_point", [0.0, 0.0]), ("long_point", [0.0, 0.0, 0.0, 0.0]),
                         ("boolean_depth", [0.0, 0.0, False]), ("text_depth", [0.0, 0.0, "0"])):
        bad = deepcopy(request)
        bad["text_points_xyz_m"][1] = value
        yield label, bad
    bad = deepcopy(request)
    bad["text_points_xyz_m"][1][0] += .001337
    yield "moved_planar_placement", bad
    bad = deepcopy(request)
    bad["text_points_xyz_m"].append(list(bad["text_points_xyz_m"][1]))
    yield "extra_display_point", bad


def main():
    parser = argparse.ArgumentParser(description="Verify explicit spatial dimension-text composition in fresh guarded SDK pair processes")
    parser.add_argument("candidate", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--manifest-sha256", required=True)
    args = parser.parse_args()
    manifest = verify_source(args.candidate, args.manifest_sha256)
    if args.output.exists():
        raise ValueError("spatial text proof directory must be unused")
    args.output.mkdir(parents=True)
    report = {"schema": "kit.sw2026.spatial-text-flow.v1", "source_manifest_sha256": args.manifest_sha256,
              "source_file_count": manifest["file_count"], "cases": [], "rejections": [], "process_count": 0,
              "passed": False, "source_original_admission": False, "native_acceptance": False,
              "heldout_acceptance": False, "hidden_inputs_read": 0, "public_drawing_writer_enabled": False}
    result_path = args.output / "Result.json"
    write_json(result_path, report)
    first_request = None
    try:
        designs = (("TextDepthCorner", .037483, .024719, .008731, "*Front", .821, (.11317, .08729)),
                   ("TextDepthCentered", .045127, .028913, .006137, "*Top", 1.137, (.12731, .09317), "center-anchored"))
        for design in designs:
            job = make_job(*design)
            baseline = None
            for label, z_value in (("Planar", 0.0), ("HeightPositive", .000237), ("HeightNegative", -.000419)):
                points = [list(job["child_policy"][key]) + [0.0] for key in ("width_text_m", "height_text_m")]
                points[1][2] = z_value
                request = {"schema": "kit.sw2026.spatial-text-request.v1", "origin_request": job,
                           "text_points_xyz_m": points}
                first_request = first_request or request
                name = design[0] + label
                case = {"name": name, "text_points_xyz_m": points, "builds": [], "passed": False}
                report["cases"].append(case)
                results = []
                for number in range(2):
                    row, value = worker("SpatialTextProcess.py", request, args.output / (name + "Build" + str(number)))
                    report["process_count"] += 1
                    case["builds"].append(row)
                    if row["return_code"] != 0 or value.get("passed") is not True:
                        raise ValueError("guarded spatial text build failed: " + value.get("diagnostic", "unknown"))
                    if value["runtime_input_file_access_attempts"] or value["sdk_research_imports"]:
                        raise ValueError("spatial text input boundary failed")
                    results.append(value)
                if results[0] != results[1]:
                    raise ValueError("spatial text independent generated pair outputs differ")
                if baseline is None:
                    original_row, original = worker("OriginPairProcess.py", job, args.output / (design[0] + "UnchangedOrigin"))
                    report["process_count"] += 1
                    case["unchanged_origin"] = original_row
                    if original_row["return_code"] != 0 or original.get("passed") is not True:
                        raise ValueError("unchanged origin reference process failed")
                    if any(original[key] != results[0][key] for key in ("child_sha256", "drawing_sha256")):
                        raise ValueError("zero-depth spatial composition changed qualified origin pair bytes")
                    baseline = results[0]
                elif results[0]["child_sha256"] == baseline["child_sha256"] or results[0]["child_shape"] != baseline["child_shape"]:
                    raise ValueError("spatial text ignored its input or changed dimensional geometry")
                prep_row, preparation = worker("SpatialTextPrepare.py", results[0], args.output / (name + "Prepare"))
                report["process_count"] += 1
                case["preparation"] = prep_row
                if prep_row["return_code"] != 0 or preparation.get("passed") is not True:
                    raise ValueError("independent spatial text preparation failed: " + preparation.get("diagnostic", "unknown"))
                for kind in ("child", "drawing"):
                    (args.output / (name + (".SLDPRT" if kind == "child" else ".SLDDRW"))).write_bytes(
                        b64decode(results[0][kind + "_base64"], validate=True))
                case.update(passed=True, child_sha256=results[0]["child_sha256"],
                            drawing_sha256=results[0]["drawing_sha256"], text_after=preparation["text_after"],
                            typed_profile=preparation["profile"], child_shape=preparation["child_shape"])
        for label, request in negative_requests(first_request):
            row, value = worker("SpatialTextProcess.py", request, args.output / ("Rejected" + label))
            report["process_count"] += 1
            rejected = row["return_code"] == 3 and value.get("passed") is False and value.get("runtime_input_file_access_attempts") == 0
            report["rejections"].append({"name": label, **row, "rejected": rejected,
                                         "diagnostic": value.get("diagnostic")})
            if not rejected:
                raise ValueError("spatial text malformed presentation did not fail closed: " + label)
        report["passed"] = True
    except Exception as error:
        report.update(exception=type(error).__name__, diagnostic=str(error))
    result_path.write_text(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n")
    print(json.dumps({key: report[key] for key in ("passed", "process_count", "native_acceptance", "source_original_admission")}))
    return 0 if report["passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
