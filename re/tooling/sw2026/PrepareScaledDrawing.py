from __future__ import annotations

import argparse
from base64 import b64decode
from copy import deepcopy
from hashlib import sha256
from itertools import product
import json
from math import cos, isclose, isfinite, sin
from pathlib import Path, PureWindowsPath
from shutil import copyfile
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[3]
TOOLS = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT / "src"), str(TOOLS / "serial")]

from CheckDrawingDefinitions import checked_artifacts
from InspectScaledDrawing import GENERATED_NAMES, ORACLE_SHA256, ORIENTATIONS, SCHEMA, SOURCE_LOCK_SHA256, TOOL_NAMES
from convert.adapters.solidworks.Container.Container import SldprtArchive


PROJECTION_SHA256 = "c18522a47dbc2848d6cc48b62b8172f49e8b8f5acd5314f4f9684839817a1b33"
JOB_SCHEMA = "kit.sw2026.scaled-drawing-neutral-job.v1"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def write_json(path, value):
    path.write_bytes(encoded(value))


def checked_json(path, expected):
    data = path.read_bytes()
    require(digest(data) == expected, f"pinned input changed: {path.name}")
    return json.loads(data)


def snapshot():
    paths = [path for folder in (ROOT / "src", TOOLS) for path in folder.rglob("*.py")]
    paths.extend((ROOT / "tests/Convert/Solidworks/Research/ConstructionGuard.py", ROOT / "pyproject.toml", ROOT / "uv.lock"))
    return {"schema": "kit.sw2026.scaled-drawing-writer-source-snapshot.v1",
            "files": {str(path.relative_to(ROOT)): digest(path.read_bytes()) for path in sorted(set(paths))}}


def canonical_rotation(orientation):
    require(orientation in ORIENTATIONS, "unsupported scaled diagnostic orientation")
    identity = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
    if orientation == "*Front":
        return identity
    if orientation == "*Top":
        angle = 1.5707963267949001
        return [1.0, 0.0, 0.0, 0.0, cos(angle), sin(angle), 0.0, -sin(angle), cos(angle)]
    if orientation == "*Right":
        angle = 1.5707963267949001
        return [cos(angle), 0.0, sin(angle), 0.0, 1.0, 0.0, -sin(angle), 0.0, cos(angle)]
    yaw, pitch = 0.78539816339745006, 0.61540309425319417
    cy, sy, cp, sp = cos(yaw), sin(yaw), cos(pitch), sin(pitch)
    return [cy, -sy * sp, sy * cp, 0.0, cp, sp, -sy, -cy * sp, cy * cp]


def rotate(rotation, point):
    return [sum(point[index] * rotation[index * 3 + axis] for index in range(3)) for axis in range(3)]


def close_vector(label, actual, expected):
    require(len(actual) == len(expected) and all(isclose(left, right, rel_tol=1e-10, abs_tol=1e-12)
            for left, right in zip(actual, expected, strict=True)), f"independent {label} preflight differs")


def prediction(request):
    drawing, part, view = (request[key] for key in ("drawing", "part", "view"))
    sheet, document = drawing["sheet"], part["document"]
    require(sheet["paper_size"] == "ansi-a-landscape" and document["plane_axis"] == "z"
            and len(document["vertices_m"]) == 4, "scaled drawing diagnostics require an ANSI A sheet and an XY rectangular child")
    vertices = document["vertices_m"]
    require(all(len(point) == 2 and all(type(value) in (int, float) and isfinite(value) for value in point) for point in vertices),
            "scaled drawing rectangle coordinates differ")
    xs, ys = zip(*vertices, strict=True)
    xmin, xmax, ymin, ymax = min(xs), max(xs), min(ys), max(ys)
    depth = document["depth_m"]
    require(type(depth) in (int, float) and isfinite(depth) and depth > 0 and xmax > xmin and ymax > ymin
            and set(map(tuple, vertices)) == set(product((xmin, xmax), (ymin, ymax))), "scaled drawing requires a nondegenerate rectangular prism")
    scale = view["scale"]
    require(type(scale) in (int, float) and isfinite(scale) and scale > 0 and isfinite(1.0 / scale), "invalid explicit view scale")
    require(len(view["position"]) == 2 and all(type(value) in (int, float) and isfinite(value) for value in view["position"]),
            "invalid explicit view position")
    dimensions = [11 * 0.0254, 8.5 * 0.0254]
    center = [(xmin + xmax) / 2, (ymin + ymax) / 2, depth / 2]
    rotation = canonical_rotation(view["orientation"])
    effective_scale = 1.0 if abs(scale - 1.0) <= 1e-8 else float(scale)
    position = [*view["position"], 0.0]
    translation = [value - effective_scale * transformed for value, transformed in zip(position, rotate(rotation, center), strict=True)]
    corners = list(product((xmin, xmax), (ymin, ymax), (0.0, depth)))
    projected = [[effective_scale * transformed + offset for transformed, offset in zip(rotate(rotation, corner), translation, strict=True)]
                 for corner in corners]
    raw = [min(point[0] for point in projected), min(point[1] for point in projected),
           max(point[0] for point in projected), max(point[1] for point in projected)]
    margin = min(dimensions) * 0.02
    outline = [value + offset for value, offset in zip(raw, (-margin, -margin, margin, margin), strict=True)]
    length, width = xmax - xmin, ymax - ymin
    expected = {
        "sheet": sheet["name"], "sheet_properties": [0, 13, sheet["scale_numerator"], sheet["scale_denominator"], 0, *dimensions, 1],
        "whats_wrong": 0,
        "view": {"name": view["name"], "orientation": view["orientation"], "position_m": list(view["position"]), "scale": scale,
                 "resolved_reference_path": part["output"]["path_name"], "configuration": document["configuration_name"],
                 "outline_m": outline, "model_to_view": [*rotation, *translation, float(scale), 0.0, 0.0, 0.0],
                 "child_volume_m3": length * width * depth,
                 "child_area_m2": 2 * (length * width + length * depth + width * depth), "child_center_m": center},
    }
    folders = drawing["folder_names"]
    tree = [[folders[key], kind, None] for key, kind in (
        ("comments", "CommentsFolder"), ("blocks", "BlockFolder"), ("binder", "DocsFolder"),
        ("annotations", "DetailCabinet"), ("ink_markups", "InkMarkupFolder"), ("review_markups", "MarkupCommentFolder"),
    )]
    tree.append([sheet["name"], "DrSheet", None])
    tree.extend([drawing["sheet_names"][key], kind, sheet["name"]] for key, kind in (
        ("plane_name", "RefPlane"), ("profile_name", "ProfileFeature"), ("detail_name", "DetailFolder"),
    ))
    tree.append([view["name"], "AbsoluteView", sheet["name"]])
    tree.extend([view["supports"][key], kind, view["name"]] for key, kind in (
        ("detail", "DetailFolder"), ("sheet_plane", "RefPlane"), ("sheet_profile", "ProfileFeature"),
        ("model_plane", "RefPlane"), ("model_profile", "ProfileFeature"),
    ))
    require(len(tree) == 16, "scaled drawing requires exactly sixteen explicitly named tree rows")
    require(0 < outline[0] < outline[2] < dimensions[0] and 0 < outline[1] < outline[3] < dimensions[1],
            "scaled diagnostic outline must fit inside the sheet")
    return {"expected": expected, "tree": tree, "corner_count": len(corners), "model_corners_m": corners,
            "projected_corners_m": projected, "raw_outline_m": raw, "border_margin_m": margin,
            "canonical_rule": "pinned native standard-view angles, independent trigonometric matrix product",
            "geometry_rule": "eight projected corners and analytic rectangular-prism mass properties",
            "independent_preflight_passed": False}


def mapped_request(request, name, windows_root):
    request = deepcopy(request)
    directory = windows_root / "Inputs" / name
    for kind, suffix, stem in (("drawing", ".SLDDRW", request["drawing"]["name"]),
                               ("part", ".SLDPRT", request["part"]["document"]["name"])):
        require(PureWindowsPath(stem).name == stem and stem not in (".", "..") and stem,
                "scaled drawing document stems must be single path components")
        require("saved_at" in request[kind]["output"], "scaled drawing requires an explicit neutral save time")
        request[kind]["output"]["path_name"] = str(directory / (stem + suffix))
    return request


def generate(request):
    data = encoded(request)
    command = [sys.executable, "-B", str(TOOLS / "DrawingFrontBundleProcess.py")]
    built = [subprocess.run(command, cwd=ROOT, input=data, capture_output=True, timeout=90) for _ in range(2)]
    for item in built:
        require(item.returncode == 0, item.stderr.decode("utf-8", errors="replace"))
    require(built[0].stdout == built[1].stdout, "two guarded scaled drawing builds differ")
    report = json.loads(built[0].stdout)
    require(report["native_acceptance"] is False and report["input_runtime_file_access_attempts"] == 0
            and report["inspection"]["readback_exact"] and report["inspection"]["detailing_bucket_count"] == 0,
            "scaled drawing guarded graph readback failed")
    artifacts = {}
    for kind in ("drawing", "part"):
        row = report[kind]
        payload = b64decode(row.pop("artifact_base64"), validate=True)
        require(digest(payload) == row["sha256"] and len(payload) == row["bytes"], "scaled drawing payload disagrees with its build report")
        archive = SldprtArchive.from_bytes(payload)
        require(row["streams"] == {name: {"bytes": len(raw), "sha256": digest(raw)} for name, raw in archive.streams.items()},
                "scaled drawing logical stream identity differs")
        artifacts[kind] = payload
    return report, artifacts, {"twice_identical": True, "guarded_build_count": 2, "stdout_sha256": digest(built[0].stdout),
                               "stderr_bytes": [len(item.stderr) for item in built], "runtime_input_file_access_attempts": 0}


def verify_prediction(report, predicted):
    observed = report["inspection"]
    expected = predicted["expected"]["view"]
    close_vector("outline", observed["outline_m"], expected["outline_m"])
    close_vector("position", observed["position_m"], expected["position_m"])
    close_vector("scale ratio", observed["scale_ratio"], [expected["scale"], 1.0])
    rotation = expected["model_to_view"][:9]
    offset = expected["model_to_view"][9:12]
    scale = expected["scale"]
    scale = 1.0 if abs(scale - 1.0) <= 1e-8 else scale
    row_major = [value for axis in range(3) for value in (*[scale * rotation[index * 3 + axis] for index in range(3)], offset[axis])]
    close_vector("SDK transform", observed["model_to_sheet"], [*row_major, 0.0, 0.0, 0.0, 1.0])
    require(observed["sheet"] == predicted["expected"]["sheet"] and observed["view"] == expected["name"],
            "scaled drawing SDK names differ")
    predicted["independent_preflight_passed"] = True


def file_summary(filename, data):
    return {"filename": filename, "bytes": len(data), "sha256": digest(data)}


def prepare(arguments):
    output = arguments.output.resolve()
    require(not output.exists() and not output.is_relative_to(ROOT), "choose an unused private scaled drawing packet directory")
    windows_root = PureWindowsPath(arguments.windows_directory)
    require(windows_root.is_absolute(), "scaled drawing packet requires an absolute encoded Windows directory")
    neutral = checked_json(arguments.job, arguments.job_sha256)
    require(neutral["schema"] == JOB_SCHEMA and tuple(case["name"] for case in neutral["cases"]) == GENERATED_NAMES,
            "scaled drawing neutral case registry differs")
    require(tuple(case["request"]["view"]["orientation"] for case in neutral["cases"]) == ORIENTATIONS,
            "scaled drawing neutral orientation order differs")
    corpus = arguments.corpus.resolve()
    lock = checked_json(corpus / "SourceLock.json", SOURCE_LOCK_SHA256)
    require(lock["passed"] and lock["pinned_inputs_immutable"] and lock["distinct_processes"] == 10
            and lock["control_results"] == [True, True] and lock["oracle_sha256"] == ORACLE_SHA256
            and all(case["split"] == "discovery" for case in lock["cases"]), "scaled native source cohort did not qualify")
    projection = checked_json(corpus.parent / "ProjectionFields01.json", PROJECTION_SHA256)
    require(projection["source_lock_sha256"] == SOURCE_LOCK_SHA256 and projection["heldout_inputs_read"] == 0,
            "scaled native source audit differs")
    control, = [case for case in lock["cases"] if case["name"] == "D00ScaledFront"]
    native, observed, _ = checked_artifacts(corpus, control)
    child_path = corpus / control["name"] / "author/GeneratedChildFile.SLDPRT"
    child = child_path.read_bytes()
    require(digest(child) == lock["reference_part_sha256"] == control["reference_part_sha256"], "scaled native control child differs")
    sources = snapshot()
    output.mkdir(parents=True, exist_ok=False)
    (output / "NeutralJob.json").write_bytes(arguments.job.read_bytes())
    (output / "SourceLock.json").write_bytes((corpus / "SourceLock.json").read_bytes())
    (output / "ProjectionFields01.json").write_bytes((corpus.parent / "ProjectionFields01.json").read_bytes())
    write_json(output / "GeneratorSourceSnapshot.json", sources)
    control_dir = output / "Inputs/NativePristine"
    control_dir.mkdir(parents=True, exist_ok=False)
    drawing_name, child_name = control["name"] + ".SLDDRW", "GeneratedChildFile.SLDPRT"
    (control_dir / drawing_name).write_bytes(native)
    (control_dir / child_name).write_bytes(child)
    rows = [{"name": "NativePristine", "directory": "Inputs/NativePristine", "kind": "native-pristine", "source_case": control["name"],
             "drawing": file_summary(drawing_name, native), "part": file_summary(child_name, child), "expected": observed,
             "source_record_sha256": control["record_sha256"], "child_resolution": "exact staged-or-original path with the locked identical child hash"}]
    builds = []
    artifacts = {name: digest((output / name).read_bytes()) for name in
                 ("NeutralJob.json", "SourceLock.json", "ProjectionFields01.json", "GeneratorSourceSnapshot.json")}
    for case in neutral["cases"]:
        name = case["name"]
        request = mapped_request(case["request"], name, windows_root)
        predicted = prediction(request)
        report, payloads, checks = generate(request)
        verify_prediction(report, predicted)
        folder = output / "Cases" / name
        folder.mkdir(parents=True, exist_ok=False)
        for filename, value in (("NeutralRequest.json", request), ("Construction.json", report), ("Prediction.json", predicted)):
            path = folder / filename
            write_json(path, value)
            artifacts[str(path.relative_to(output))] = digest(path.read_bytes())
        destination = output / "Inputs" / name
        destination.mkdir(parents=True, exist_ok=False)
        row = {"name": name, "directory": str(destination.relative_to(output)), "kind": "neutral-generated",
               "expected": predicted["expected"], "tree": predicted["tree"],
               "neutral_request": str((folder / "NeutralRequest.json").relative_to(output)),
               "construction": str((folder / "Construction.json").relative_to(output)),
               "prediction": str((folder / "Prediction.json").relative_to(output))}
        for kind, data in payloads.items():
            filename = PureWindowsPath(request[kind]["output"]["path_name"]).name
            (destination / filename).write_bytes(data)
            row[kind] = file_summary(filename, data)
        rows.append(row)
        builds.append({"case": name, **checks})
    require(snapshot() == sources, "writer source changed during scaled drawing preparation")
    require(digest(arguments.job.read_bytes()) == arguments.job_sha256
            and checked_artifacts(corpus, control)[0] == native and digest(child_path.read_bytes()) == digest(child),
            "scaled drawing neutral/native input changed during preparation")
    preparation = {"schema": "kit.sw2026.scaled-drawing-preparation-checks.v1", "cases": builds,
                   "guarded_build_count": 8, "all_twice_identical": True, "runtime_input_file_access_attempts": 0,
                   "writer_sources_immutable": True, "neutral_job_immutable": True, "native_control_immutable": True,
                   "heldout_inputs_read": 0, "vendor_runtime_executed": False}
    write_json(output / "PreparationChecks.json", preparation)
    artifacts["PreparationChecks.json"] = digest((output / "PreparationChecks.json").read_bytes())
    tools_dir = output / "Tools"
    tools_dir.mkdir(exist_ok=False)
    for name in TOOL_NAMES:
        copyfile(TOOLS / name, tools_dir / name)
    tools = {name: digest((tools_dir / name).read_bytes()) for name in TOOL_NAMES}
    write_json(tools_dir / "GuestTools.json", tools)
    packet = {"schema": SCHEMA, "native_acceptance": False, "heldout_inputs_tested": 0, "writer_output_count": 8,
              "source_lock_sha256": SOURCE_LOCK_SHA256, "oracle_sha256": ORACLE_SHA256, "source_artifacts": artifacts,
              "encoded_windows_directory": str(windows_root), "expected_fresh_processes": 12, "inputs": rows}
    write_json(output / "Trial.json", packet)
    packet_sha = digest((output / "Trial.json").read_bytes())
    tools_sha = digest((tools_dir / "GuestTools.json").read_bytes())
    runner_sha = tools["InspectScaledDrawing.py"]
    verified = subprocess.run([sys.executable, "-B", str(tools_dir / "InspectScaledDrawing.py"), str(output / "Trial.json"),
                               "--packet-sha256", packet_sha, "--tools-sha256", tools_sha, "--runner-sha256", runner_sha, "--verify-only"],
                              cwd=output, capture_output=True, timeout=30)
    require(verified.returncode == 0, verified.stderr.decode("utf-8", errors="replace"))
    return {"packet": str(output / "Trial.json"), "packet_sha256": packet_sha, "tools_sha256": tools_sha,
            "runner_sha256": runner_sha, "source_snapshot_sha256": artifacts["GeneratorSourceSnapshot.json"],
            "guarded_build_count": 8, "runtime_input_file_access_attempts": 0, "host_verify_only": json.loads(verified.stdout),
            "inputs": [{key: row[key] for key in ("name", "drawing", "part")} for row in rows]}


def main():
    parser = argparse.ArgumentParser(description="Freeze four independently predicted generated scaled drawing pairs for the owned oracle")
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--job", type=Path, required=True)
    parser.add_argument("--job-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--windows-directory", required=True)
    arguments = parser.parse_args()
    print(json.dumps(prepare(arguments), indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
