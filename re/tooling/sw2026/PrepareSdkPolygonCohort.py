from __future__ import annotations

import argparse
from base64 import b64decode
from dataclasses import replace
from fractions import Fraction
from hashlib import sha256
import json
import math
from pathlib import Path
import subprocess
import sys

from AuthorCurves import digest, require


LOCK_SHA256 = "abc1724a8856083a9c5e7054cd85b3035dc7da8423063f0caabd07a3e6f9dc40"
SOURCE_SHA256 = "c45dd7702e3238ec1713fb1b03850a941f3837498241d80c736a2a69c494b145"
PROCESS_SHA256 = "cccce28c0dbe396392a01eecf024e7577624a034a5e00129dc597702122535bd"
SLOTS = ("H3_scalene", "H5_irregular", "H7_irregular")


def read_locked(path, expected):
    raw = path.read_bytes()
    require(sha256(raw).hexdigest() == expected, f"frozen identity differs: {path.name}")
    return json.loads(raw)


def encode(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def write(path, raw):
    with path.open("xb") as file:
        file.write(raw)
    return sha256(raw).hexdigest()


def prism(points, depth):
    exact = tuple(tuple(Fraction(coord) / 1000 for coord in row) for row in points)
    pairs = tuple(zip(exact, (*exact[1:], exact[0]), strict=True))
    weights = tuple(a[0] * b[1] - b[0] * a[1] for a, b in pairs)
    signed_double_area = sum(weights)
    require(signed_double_area != 0, "locked polygon must enclose a nonzero area")
    area = float(abs(signed_double_area) / 2)
    perimeter = math.fsum(math.dist(a, b) for a, b in pairs)
    centroid = [
        float(sum((a[i] + b[i]) * weight for (a, b), weight in zip(pairs, weights, strict=True)) / (3 * signed_double_area))
        for i in (0, 1)
    ]
    return {"body_count": 1, "volume_m3": area * depth, "area_m2": 2 * area + perimeter * depth,
            "centre_of_mass_m": [*centroid, depth / 2]}


def neutral(row):
    from interchange.serialization.Deserialize import FromData
    from interchange.serialization.EncodeData import ToData
    from tests.Convert.Solidworks.Research.Construction.Part.MakePolygonCase import MakePolygonCase

    name = Path(row["name"]).stem
    sketch, boss = row["spec"]["ops"]
    require(row["kind"] == "held-out" and name in SLOTS and sketch["op"] == "sketch" and sketch["plane"] == "front"
            and not sketch["dims"] and boss["op"] == "extrude" and boss["sketch"] == sketch["name"],
            "expected a locked plain Front line loop and its blind boss")
    segments = sketch["entities"]
    require(len(segments) >= 3 and all(value["t"] == "line" and len(value["p"]) == 4 for value in segments),
            "the locked sketch must supply ordinary line endpoints")
    points = tuple(tuple(value["p"][:2]) for value in segments)
    require(all(tuple(value["p"][2:]) == points[(index + 1) % len(points)] for index, value in enumerate(segments)),
            "the ordered locked lines must form an actual closed profile")
    depth = boss["depth"]
    require(type(depth) in (int, float) and math.isfinite(depth) and depth > 0, "locked boss depth is invalid")
    request = MakePolygonCase(name, points, False)
    doc = FromData(request["document"])
    feature, = doc.feature_timeline
    parameter, = doc.parameters
    length = replace(parameter.value, value=depth)
    request["document"] = ToData(replace(
        doc, configurations=(replace(doc.configurations[0], name="Default"),),
        sketches=(replace(doc.sketches[0], name=sketch["name"]),),
        feature_timeline=(replace(feature, definition=replace(feature.definition, length=length)),),
        parameters=(replace(parameter, value=length),),
    ))
    system = request["settings"]["system"]
    system["folders"] = [[tag, "Lights and Cameras" if tag == "moEnvFolder_c" else caption]
                         for tag, caption in system["folders"]]
    expected = prism(points, depth / 1000)
    observed = row["source_mass"]
    measured = [observed["volume"], observed["area"], *observed["com"]]
    calculated = [expected["volume_m3"], expected["area_m2"], *expected["centre_of_mass_m"]]
    require(row["source_bodies"] == 1 and all(math.isclose(a, b, rel_tol=5e-7, abs_tol=1e-15)
                                             for a, b in zip(measured, calculated, strict=True)),
            "the locked source geometry disagrees with its neutral prism")
    case = {"intent": {"self_path": request["settings"]["output"]["path_name"], "model_name": name,
                       "configuration_name": "Default", "profile": sketch["name"], "feature": feature.name,
                       "support": system["planes"]["z"], "resolved_roots": 19, "sketch_lines": len(points),
                       "vertices_m": [[x * 0.001, y * 0.001] for x, y in points],
                       "fixed_relations_in_user_sketch": 0, "depth_m": depth / 1000},
            "expected_initial": expected,
            "edit": {"dimension": "D1@" + feature.name, "new_depth_m": depth / 800, "expected": prism(points, depth / 800)},
            "source_native_sha256": row["sha256"], "source_native_bytes": row["bytes"]}
    return request, case


def execute(root, output, key, tool, request, polygon=False):
    program = root / "re/tooling/sw2026" / tool
    args = [sys.executable, "-I", "-B", str(program), str(root)]
    if polygon:
        args.append("polygon")
    result = subprocess.run(args, input=request, cwd=root, capture_output=True, timeout=180)
    stdout = write(output / (key + ".stdout"), result.stdout)
    write(output / (key + ".stderr"), result.stderr)
    require(result.returncode == 0 and not result.stderr, f"guarded polygon {key} failed")
    parsed = json.loads(result.stdout)
    require(parsed["passed"] and not parsed["runtime_input_file_reads"] and not parsed["public_writer_qualified"]
            and not parsed["native_acceptance"], f"guarded polygon {key} did not meet its scope")
    return parsed, stdout


def prepare(args):
    root = args.code.resolve(strict=True)
    manifest = read_locked(root.parent / "FrozenSource.json", SOURCE_SHA256)
    for name, expected in manifest["files_sha256"].items():
        require(digest(root / name) == expected, f"the frozen polygon writer differs: {name}")
    pure = read_locked(args.process_proof, PROCESS_SHA256)
    require(pure["passed"] and pure["source_closure_sha256"] == SOURCE_SHA256 and not pure["heldout_inputs_read"],
            "expected the successful exact polygon process closure")
    disclosed = read_locked(args.disclosed_result, args.disclosed_sha256)
    require(disclosed["passed"] and disclosed["controls_healthy"] and disclosed["distinct_processes"] == 4
            and not disclosed["heldout_inputs_read"], "the independent disclosed SDK polygon lifecycle must pass")
    lock = read_locked(args.source_lock, LOCK_SHA256)
    require(lock["writer_state"].endswith("polygon family emitter is not implemented") and len(lock["records"]) == 5,
            "the source lock must predate the original polygon emitter")
    rows = {Path(row["name"]).stem: row for row in lock["records"] if row["kind"] == "held-out"}
    require(tuple(rows) == SLOTS, "the original polygon cohort changed")
    args.output.mkdir()
    sys.path[:0] = [str(root), str(root / "src")]
    summary = {"schema": "kit.sw2026.sdk-polygon-cohort-generation.v1",
               "source_lock_sha256": LOCK_SHA256, "frozen_source_sha256": SOURCE_SHA256,
               "preparer_sha256": digest(Path(__file__)), "disclosed_result_sha256": args.disclosed_sha256,
               "cases": [], "original_native_files_read": 0, "passed": False}
    for slot, row in rows.items():
        output = args.output / slot
        output.mkdir()
        request, case = neutral(row)
        payload = encode(request)
        request_sha = write(output / "NeutralRequest.json", payload)
        case_sha = write(output / "Expected.json", encode(case))
        a, a_sha = execute(root, output, "BuildA", "SdkBlindPartProcess.py", payload, True)
        b, b_sha = execute(root, output, "BuildB", "SdkBlindPartProcess.py", payload, True)
        require(a == b and a_sha == b_sha, "complete polygon reconstruction differs across fresh workers")
        packed = encode({"request": request, "build": a})
        write(output / "ReadbackRequest.json", packed)
        prepared, prepared_sha = execute(root, output, "Prepare", "SdkBlindPartPrepare.py", packed, True)
        independent, independent_sha = execute(root, output, "Counterpart", "SdkBlindPartCounterpart.py", packed)
        raw = b64decode(a["blob"], validate=True)
        require(len(raw) == a["bytes"] and sha256(raw).hexdigest() == a["sha256"] and prepared["artifact_sha256"] == a["sha256"]
                and len(prepared["streams"]) == len(independent["streams"]) == 10, "incomplete polygon preparation")
        output_sha = write(output / "Candidate.SLDPRT", raw)
        summary["cases"].append({"slot": slot, "request_sha256": request_sha, "expected_sha256": case_sha,
                                 "original_source_sha256": case["source_native_sha256"], "generated_sha256": output_sha,
                                 "bytes": len(raw), "build_a_sha256": a_sha, "build_b_sha256": b_sha,
                                 "prepare_sha256": prepared_sha, "counterpart_sha256": independent_sha, "guarded_workers": 4,
                                 "runtime_input_reads": 0, "streams": 10})
    summary["passed"] = True
    proof = write(args.output / "Generation.json", encode(summary))
    print(json.dumps({"passed": True, "report_sha256": proof, "cases": len(summary["cases"]),
                      "native_sources_read": 0, "guarded_processes": 12}, sort_keys=True))


def main():
    parser = argparse.ArgumentParser(description="Freeze SDK outputs from all three original polygon neutral requests")
    parser.add_argument("--code", type=Path, required=True)
    parser.add_argument("--source-lock", type=Path, required=True)
    parser.add_argument("--process-proof", type=Path, required=True)
    parser.add_argument("--disclosed-result", type=Path, required=True)
    parser.add_argument("--disclosed-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    prepare(parser.parse_args())


if __name__ == "__main__":
    main()
