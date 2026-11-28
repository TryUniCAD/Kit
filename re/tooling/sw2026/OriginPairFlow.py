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
from dataclasses import replace
from hashlib import sha256
import json
import subprocess

from OriginPairInput import make_job
from interchange.serialization.Deserialize import FromData
from interchange.serialization.EncodeData import ToData


def digest(data):
    return sha256(data).hexdigest()


def write_json(path, value):
    with path.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def verify_code(candidate, expected):
    path = candidate / "SourceManifest.json"
    if digest(path.read_bytes()) != expected or ROOT.resolve() != (candidate / "CodeRoot").resolve():
        raise ValueError("run the exact origin flow from its immutable source closure")
    metadata = json.loads(path.read_bytes())
    seen = set()
    for row in metadata["files"]:
        name = Path(row["path"])
        raw_source = ROOT / name
        source = raw_source.resolve(strict=True)
        if raw_source.is_symlink() or name.is_absolute() or not source.is_relative_to(ROOT.resolve()) or row["path"] in seen:
            raise ValueError("origin source closure path membership differs")
        data = source.read_bytes()
        if source.is_symlink() or len(data) != row["bytes"] or digest(data) != row["sha256"]:
            raise ValueError("origin source closure bytes differ: " + str(name))
        seen.add(row["path"])
    if len(seen) != metadata["file_count"]:
        raise ValueError("origin source closure count differs")
    return metadata


def worker(name, request, prefix):
    encoded = json.dumps(request, sort_keys=True, ensure_ascii=False, allow_nan=False).encode("utf-8")
    prefix.with_suffix(".Request.json").write_bytes(encoded)
    result = subprocess.run([sys.executable, "-I", "-B", str(TOOLS / name)], input=encoded,
                            capture_output=True, cwd=ROOT, timeout=180)
    prefix.with_suffix(".stdout.json").write_bytes(result.stdout)
    prefix.with_suffix(".stderr.txt").write_bytes(result.stderr)
    row = {"return_code": result.returncode, "stdout_sha256": digest(result.stdout), "stderr_sha256": digest(result.stderr),
           "request_sha256": digest(encoded), "worker_sha256": digest((TOOLS / name).read_bytes())}
    try:
        data = json.loads(result.stdout)
    except (ValueError, UnicodeError):
        data = {"passed": False, "diagnostic": "worker did not return JSON"}
    return row, data


def rejected_jobs(job):
    for key, value in (("selection", "ordinary-child-sketch"), ("population_argument", 1),
                       ("population_argument", False), ("feature_id", 17), ("creation_time", 2592000)):
        bad = deepcopy(job)
        bad["origin_display"][key] = value
        yield "origin_" + key + "_" + str(value), bad
    bad = deepcopy(job)
    bad["child_policy"]["kind"] = "unknown-anchored"
    yield "unknown_child_anchor", bad
    for label in ("path", "configuration"):
        bad = deepcopy(job)
        drawing = FromData(bad["drawing_document"])
        if label == "path":
            drawing = replace(drawing, ModelRefs=(replace(drawing.ModelRefs[0], SourcePath=r"C:\ForeignChild.SLDPRT"),))
        else:
            sheet = drawing.Sheets[0]
            drawing = replace(drawing, Sheets=(replace(sheet, Views=(replace(sheet.Views[0], ConfigurationName="foreign configuration"),)),))
        bad["drawing_document"] = ToData(drawing)
        yield "wrong_child_" + label, bad


def center_rejected_jobs(job):
    bad = deepcopy(job)
    bad["child_policy"]["kind"] = "corner-anchored"
    yield "center_as_corner", bad
    bad = deepcopy(job)
    document = FromData(bad["part"]["document"])
    sketch = document.sketches[0]
    entities = tuple(replace(entity, geometry=replace(entity.geometry,
                         start=replace(entity.geometry.start, x=entity.geometry.start.x + 1.0),
                         end=replace(entity.geometry.end, x=entity.geometry.end.x + 1.0))) for entity in sketch.entities)
    bad["part"]["document"] = ToData(replace(document, sketches=(replace(sketch, entities=entities),)))
    yield "center_shifted_from_origin", bad
    bad = deepcopy(job)
    bad["child_policy"]["height_text_m"][0] = 0.0
    yield "center_text_inside_rectangle", bad
    bad = deepcopy(job)
    document = FromData(bad["part"]["document"])
    sketch = document.sketches[0]
    bad["part"]["document"] = ToData(replace(document, sketches=(replace(sketch, constraints=sketch.constraints[:-1]),)))
    yield "center_missing_driver", bad


def main():
    parser = argparse.ArgumentParser(description="Construct and independently decode fresh origin display pairs through guarded SDK processes")
    parser.add_argument("candidate", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--previous-result", type=Path, required=True)
    args = parser.parse_args()
    metadata = verify_code(args.candidate, args.manifest_sha256)
    previous_bytes = args.previous_result.read_bytes()
    if digest(previous_bytes) != metadata["prior_origin_result_sha256"]:
        raise ValueError("prior corner process receipt changed")
    previous = json.loads(previous_bytes)
    if previous.get("passed") is not True or previous["source_manifest_sha256"] != metadata["prior_origin_source_manifest_sha256"]:
        raise ValueError("prior corner process source qualification differs")
    previous_cases = {row["name"]: row for row in previous["cases"]}
    if args.output.exists():
        raise ValueError("origin process output must be unused")
    args.output.mkdir(parents=True)
    report = {"schema": "kit.sw2026.sdk-origin-process-flow.v1", "source_manifest_sha256": args.manifest_sha256,
              "source_lock_sha256": metadata["hidden_source_lock_sha256"], "cases": [], "rejections": [],
              "passed": False, "native_acceptance": False, "heldout_acceptance": False,
              "public_drawing_writer_enabled": False, "hidden_inputs_read": 0}
    path = args.output / "Result.json"
    with path.open("x") as handle:
        json.dump(report, handle, indent=2)
    specifications = (("OriginConstructorAlpha", .035731, .021419, .006983, "*Front", .743, (.093719, .073241)),
                      ("OriginConstructorBetaΩ", .029173, .042683, .009527, "*Top", 1.183, (.123917, .096431)),
                      ("OriginCenterGamma", .041731, .027389, .008173, "*Right", .913, (.097413, .083291), "center-anchored"),
                      ("OriginCenterDeltaΩ", .052193, .019731, .005987, "*Front", .613, (.132719, .091373), "center-anchored"))
    first_job, center_job = None, None
    for spec in specifications:
        job = make_job(*spec)
        first_job = first_job or job
        if job["child_policy"]["kind"] == "center-anchored":
            center_job = center_job or job
        label = spec[0]
        rows, values = [], []
        for index in range(2):
            row, value = worker("OriginPairProcess.py", job, args.output / (label + "Build" + str(index)))
            rows.append(row)
            values.append(value)
        case = {"name": label, "builds": rows, "passed": False}
        report["cases"].append(case)
        if any(row["return_code"] != 0 for row in rows) or any(value.get("passed") is not True for value in values):
            break
        if values[0] != values[1]:
            case["diagnostic"] = "repeat guarded construction differs"
            break
        value = values[0]
        if label in previous_cases:
            same = all(value[key] == previous_cases[label][key] for key in ("drawing_sha256", "child_sha256"))
            case["prior_corner_pair_bytes_unchanged"] = same
            if not same:
                case["diagnostic"] = "prior corner pair artifact bytes changed"
                break
        for key, suffix in (("drawing", ".SLDDRW"), ("child", ".SLDPRT")):
            data = b64decode(value[key + "_base64"], validate=True)
            if digest(data) != value[key + "_sha256"]:
                raise ValueError("generated origin artifact digest differs")
            (args.output / (label + suffix)).write_bytes(data)
        row, prepared = worker("OriginPairPrepare.py", value, args.output / (label + "Prepare"))
        case.update({"preparation": row, "prepared": prepared,
                     "drawing_sha256": value["drawing_sha256"], "child_sha256": value["child_sha256"],
                     "profile": value["profile"], "child_shape": value["child_shape"], "child_neutral": value["child_neutral"],
                     "changed_default_streams": value["changed_default_streams"],
                     "runtime_input_file_access_attempts": value["runtime_input_file_access_attempts"],
                     "sdk_research_imports": value["sdk_research_imports"],
                     "passed": row["return_code"] == 0 and prepared.get("passed") is True})
        if not case["passed"]:
            break
        counterpart_row, counterpart = worker("OriginChildCounterpart.py", {"request": job, "build": value}, args.output / (label + "Counterpart"))
        case.update({"counterpart": counterpart_row, "independent_child": counterpart,
                     "passed": counterpart_row["return_code"] == 0 and counterpart.get("passed") is True})
        if not case["passed"]:
            break
    if len(report["cases"]) == 4 and all(row["passed"] for row in report["cases"]):
        for index, (name, job) in enumerate((*rejected_jobs(first_job), *center_rejected_jobs(center_job))):
            row, value = worker("OriginPairProcess.py", job, args.output / ("Reject" + str(index)))
            report["rejections"].append({"case": name, **row, "diagnostic": value.get("diagnostic"),
                                         "rejected": row["return_code"] != 0 and value.get("passed") is False
                                         and "drawing_base64" not in value})
        report["passed"] = len(report["rejections"]) == 12 and all(row["rejected"] for row in report["rejections"])
    report["process_count"] = sum(len(row["builds"]) + int("preparation" in row) + int("counterpart" in row) for row in report["cases"]) + len(report["rejections"])
    path.write_text(json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    print(json.dumps({"passed": report["passed"], "result_sha256": digest(path.read_bytes()),
                      "process_count": report["process_count"], "native_acceptance": False}))
    return 0 if report["passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
