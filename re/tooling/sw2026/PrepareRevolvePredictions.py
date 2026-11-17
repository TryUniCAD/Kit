from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
from pathlib import Path, PureWindowsPath
from runpy import run_path
from subprocess import run
from sys import executable
from sysconfig import get_paths


GENERATOR = "cd0cf5738f074ac9d4fe44490db2bb89cc18dfe6"
GENERATOR_TREE = "efc6a8f176e7859e5d79069a707a462c259eb4b7"
SOURCE_LOCK = "bf4a857b222a9ea61d5d74007fbde4090d95d1563aa8025de3b01454e1839b2f"
TEST_ROOT = Path("tests/Convert/Solidworks/Research")
PLANE_AXES = {"front": "z", "top": "y", "right": "x"}
WORLD_AXES = {
    "front": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
    "top": [[1, 0, 0], [0, 0, -1], [0, 1, 0]],
    "right": [[0, 0, -1], [0, 1, 0], [1, 0, 0]],
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_value(path, value):
    encoded = (json.dumps(value, indent=2, allow_nan=False) + "\n").encode()
    with path.open("xb") as output:
        output.write(encoded)
    return digest(encoded)


def request_for(case, facade, make_part, make_tree):
    inner, outer = case["radius_m"]
    low, high = case["axial_m"]
    abscissa = case["axis_x_m"]
    axis_low, axis_high = case["axis_axial_m"]
    left, right = abscissa + inner, abscissa + outer
    vertices = [[left, low], [right, low], [right, high], [left, high]]
    request = make_tree(make_part(vertices, 0.01, facade.stem))
    document = request["document"]
    del document["extrusion_name"], document["depth_m"]
    document.update(
        feature_kind="revolve",
        configuration_name="Default",
        sketch_name="RevolveSketch",
        revolution_name="OrdinaryBossRevolve",
        axis_start_m=[abscissa, axis_low],
        axis_end_m=[abscissa, axis_high],
        angle_rad=math.radians(case["angle_deg"]),
        reverse_direction=case["reverse"],
        plane_axis=PLANE_AXES[case["plane"]],
    )
    request["output"] = {"path_name": str(facade), "saved_at": request["provenance"]["modified_at"] + 1}
    return request


def geometry_for(case, angle_degrees):
    inner, outer = case["radius_m"]
    low, high = case["axial_m"]
    theta = math.radians(angle_degrees)
    radius_delta = outer**2 - inner**2
    height = high - low
    section_area = height * (outer - inner)
    area = theta * (height * (inner + outer) + radius_delta)
    center = [case["axis_x_m"], (low + high) / 2, 0.0]
    if angle_degrees < 360:
        area += 2 * section_area
        distance = 2 * (outer**3 - inner**3) / (3 * theta * radius_delta)
        center[0] += distance * math.sin(theta)
        center[2] += (1 if case["reverse"] else -1) * distance * (1 - math.cos(theta))
    return {
        "angle_radians": theta,
        "volume": height * theta * radius_delta / 2,
        "area": area,
        "com": [sum(value * basis[index] for value, basis in zip(center, WORLD_AXES[case["plane"]], strict=True)) for index in range(3)],
        "bodies": 1,
    }


def construct_case(case, facade, source_root, request, validate_frame, work):
    program = source_root / TEST_ROOT / "FreshPartProcess.py"
    completed = run(
        [executable, "-I", "-B", str(program), str(source_root)], cwd=source_root,
        input=json.dumps(request), text=True, capture_output=True, timeout=120, check=False,
    )
    if completed.returncode:
        raise ValueError(completed.stderr)
    report = json.loads(completed.stdout)
    streams = report["streams"]
    imports = [Path(entry) for entry in report["module_reads"]]
    paths = get_paths()
    runtime_paths = (source_root, *(Path(paths[name]) for name in ("stdlib", "platstdlib", "purelib", "platlib")))
    if report["denied_reads"] or not any(entry.is_relative_to(source_root / "src") for entry in imports):
        raise ValueError("generation did not use the pinned modeled source")
    if any(not any(entry.is_relative_to(path) for path in runtime_paths) for entry in imports):
        raise ValueError("generation was not isolated to the pinned modeled source")
    if len(streams) != 9 or any(not row["byte_identity_passed"] or row["tail"] for row in streams.values()):
        raise ValueError("generated archive did not round-trip every modeled stream")
    if report["features"].count("moInkMarkupFolder_c") != 1 or "moNotesAreaFtrFolder_c" in report["features"]:
        raise ValueError("generated presentation did not have one native markup owner")
    validate_frame(PLANE_AXES[case["plane"]], report["profile_model_to_sketch"])
    feature = report["revolution"]
    doc = request["document"]
    expected_length = doc["axis_end_m"][1] - doc["axis_start_m"][1]
    if not (
        feature["profile_owned"] and feature["profile_reference_id"] == feature["profile_id"]
        and feature["feature_id"] == feature["keyword_feature_id"]
        and feature["profile_reference_time"] == 2592000
        and feature["selected_line_id"] == 4 and feature["line_mark"] == feature["axis_mark"] == 5
        and feature["angle_rad"] == feature["cached_angle_rad"] == doc["angle_rad"]
        and feature["axis_start"] == dict(zip("xyz", [*doc["axis_start_m"], 0], strict=True))
        and feature["axis_direction"] == {"x": 0, "y": 1, "z": 0}
        and math.isclose(feature["axis_length"], expected_length, rel_tol=2e-7, abs_tol=1e-12)
        and feature["reverse"] == int(case["reverse"]) and feature["keyword_frame"]
        and report["lines"] == 5 and all(report["plane_ownership"].values())
    ):
        raise ValueError("generated sketch, axis or driving parameter ownership differs from its input")
    native = base64.b64decode(report.pop("blob"), validate=True)
    with (work / facade.name).open("xb") as output:
        output.write(native)
    receipt = write_value(work / (facade.stem + ".archive.json"), report)
    return digest(native), receipt


def main():
    parser = argparse.ArgumentParser(description="Generate ordinary revolve candidates from locked authored inputs")
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--source-lock", required=True, type=Path)
    parser.add_argument("--specs", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--guest-directory", required=True, type=PureWindowsPath)
    parser.add_argument("--split", choices=("discovery", "heldout"), required=True)
    args = parser.parse_args()
    root = args.source_root.resolve(strict=True)
    frozen = args.source_lock.read_bytes()
    if digest(frozen) != SOURCE_LOCK:
        raise ValueError("source lock hash differs")
    lock = json.loads(frozen)
    authored = args.specs.read_bytes()
    if args.split == "heldout" and digest(authored) != lock["specs_sha256"]:
        raise ValueError("held-out authored specification hash differs")
    cases = [case for case in json.loads(authored)["cases"] if case["split"] == args.split]
    expected_names = [entry["name"] for entry in lock["cases"] if entry["split"] == args.split]
    if [case["name"] for case in cases] != expected_names or not args.guest_directory.is_absolute():
        raise ValueError("selected cohort or staged guest output differs from the prediction contract")
    make_part = run_path(str(root / TEST_ROOT / "FreshPartInput.py"))["MakePartInput"]
    make_tree = run_path(str(root / TEST_ROOT / "Presentation/MakeTreeInput.py"))["MakeTreeInput"]
    validate_frame = run_path(str(root / TEST_ROOT / "Presentation/Frame/CheckFrame.py"))["CheckFrame"]
    args.output.mkdir(parents=True, exist_ok=False)
    predictions = []
    for case in cases:
        facade = args.guest_directory / f"Kit{case['name']}.SLDPRT"
        request = request_for(case, facade, make_part, make_tree)
        targets = {label: geometry_for(case, case[key]) for label, key in (("original", "angle_deg"), ("edited", "edit_angle_deg"))}
        targets.update(frame_points=[[0, 0, 0], *WORLD_AXES[case["plane"]]], configuration="Default")
        request_hash = write_value(args.output / (facade.stem + ".request.json"), request)
        target_hash = write_value(args.output / (facade.stem + ".targets.json"), targets)
        candidate_hash, receipt_hash = construct_case(case, facade, root, request, validate_frame, args.output)
        predictions.append({
            "source_case": case["name"], "model": case | {"name": facade.stem},
            "source": str(facade), "sha256": candidate_hash, "request_sha256": request_hash,
            "targets_sha256": target_hash, "generator_receipt_sha256": receipt_hash,
        })
    manifest = write_value(args.output / "Predictions.json", {
        "schema": "kit.sw2026.ordinary-revolve-predictions.v1", "split": args.split,
        "generator_revision": GENERATOR, "generator_tree": GENERATOR_TREE,
        "tool_sha256": digest(Path(__file__).read_bytes()), "source_lock_sha256": SOURCE_LOCK,
        "specs_sha256": digest(authored), "predictions": predictions,
    })
    print(json.dumps({"predictions_sha256": manifest, "count": len(predictions), "split": args.split}))


if __name__ == "__main__":
    main()
