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

from EpochClocks import require
from EpochPairInput import make_epoch_request
from convert.adapters.solidworks.Container.Container import SldprtArchive


def digest(value):
    return sha256(value).hexdigest()


def encode(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def write_new(path, value):
    with path.open("xb") as handle:
        handle.write(value)


def verify_source(candidate, expected):
    raw = (candidate / "SourceManifest.json").read_bytes()
    require(digest(raw) == expected and ROOT.resolve() == (candidate / "CodeRoot").resolve(),
            "run the exact epoch controller from its frozen source closure")
    manifest = json.loads(raw)
    seen = set()
    for row in manifest["files"]:
        relative = Path(row["path"])
        path = ROOT / relative
        require(not relative.is_absolute() and ".." not in relative.parts
                and not path.is_symlink() and path.resolve(strict=True).is_relative_to(ROOT.resolve())
                and row["path"] not in seen, "epoch source closure path differs")
        value = path.read_bytes()
        require(len(value) == row["bytes"] and digest(value) == row["sha256"],
                "epoch source closure bytes differ: " + row["path"])
        seen.add(row["path"])
    require(len(seen) == manifest["file_count"], "epoch source closure count differs")
    require(seen == {str(path.relative_to(ROOT)) for path in ROOT.rglob("*") if path.is_file()},
            "epoch source closure has undeclared files")
    return manifest


def worker(name, request, prefix):
    stdin = encode(request)
    write_new(prefix.with_suffix(".Request.json"), stdin)
    result = subprocess.run([sys.executable, "-I", "-B", str(TOOLS / name)],
                            input=stdin, capture_output=True, cwd=ROOT, timeout=180)
    write_new(prefix.with_suffix(".stdout.json"), result.stdout)
    write_new(prefix.with_suffix(".stderr.txt"), result.stderr)
    record = {"worker": name, "worker_sha256": digest((TOOLS / name).read_bytes()),
              "request_sha256": digest(stdin), "stdout_sha256": digest(result.stdout),
              "stderr_sha256": digest(result.stderr), "return_code": result.returncode,
              "artifact_prefix": prefix.name}
    try:
        value = json.loads(result.stdout)
    except (ValueError, UnicodeError):
        value = {"passed": False, "diagnostic": "worker did not emit JSON"}
    return record, value


def negative_requests(request):
    bad = deepcopy(request)
    bad["clock_plan"]["ModifiedAt"] = True
    yield "boolean_clock", bad
    bad = deepcopy(request)
    del bad["clock_plan"]["RootFirstEventAt"]
    yield "missing_root_event", bad
    bad = deepcopy(request)
    bad["clock_plan"]["captured_epoch"] = 1760000123
    yield "unknown_clock_field", bad
    bad = deepcopy(request)
    bad["clock_plan"]["ModifiedAt"] = 2592000
    yield "unqualified_sentinel_year", bad
    bad = deepcopy(request)
    bad["clock_plan"]["SelfCreatedAt"] += 1
    yield "wrong_self_creation", bad
    bad = deepcopy(request)
    bad["clock_plan"]["CreatedAt"] += 1
    bad["clock_plan"]["SelfCreatedAt"] += 1
    yield "clock_model_disagrees_with_neutral_creation", bad
    bad = deepcopy(request)
    bad["drawing_clock_plan"]["ManagerSavedAt"] = bad["drawing_clock_plan"]["SelfSavedAt"]
    yield "unused_drawing_manager_clock", bad
    bad = deepcopy(request)
    bad["origin_request"]["origin_display"]["creation_time"] = bad["clock_plan"]["RootFirstEventAt"]
    yield "root_clock_substituted_for_origin_event", bad


def compare_defaults(build, baseline, axis):
    require(build["profile"] == baseline["profile"] and build["child_shape"] == baseline["child_shape"],
            "epoch composition changed origin or anchored geometry owners")
    require(build["drawing_sha256"] == baseline["drawing_sha256"]
            and build["drawing_base64"] == baseline["drawing_base64"]
            and build["streams"] == baseline["streams"],
            "child clock experiment changed the fixed complete drawing")
    first = SldprtArchive.from_bytes(b64decode(build["child_base64"], validate=True)).streams
    second = SldprtArchive.from_bytes(b64decode(baseline["child_base64"], validate=True)).streams
    require(set(first) == set(second), "clock experiment changed child stream membership")
    changed = {name for name in first if first[name] != second[name]}
    allowed = {"none": set(), "ModifiedAt": {"Header2", "Contents/Config-0-ModelHeader"},
               "RootFirstEventAt": {"Header2", "Contents/Config-0-ModelHeader"},
               "VersionHistoryFirstEventAt": {"_MO_VERSION_19000/History"}}[axis]
    require(changed == allowed, "clock experiment changed an unexplained child stream: " + repr(changed))
    require(build["runtime_input_file_access_attempts"] == baseline["runtime_input_file_access_attempts"] == 0
            and build["sdk_research_imports"] == baseline["sdk_research_imports"] == [],
            "clock comparison lost the no-input-read construction boundary")
    return {"changed_child_streams": sorted(changed), "drawing_bytes_unchanged": True,
            "other_child_streams_unchanged": True, "actual_origin_and_geometry_unchanged": True}


def main():
    parser = argparse.ArgumentParser(description="Frozen source-only epoch composition and independent linked readback")
    parser.add_argument("candidate", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--manifest-sha256", required=True)
    args = parser.parse_args()
    manifest = verify_source(args.candidate, args.manifest_sha256)
    spec = json.loads((TOOLS / "EpochExperimentSpec01.json").read_bytes())
    require(spec["schema"] == "kit.sw2026.sdk-epoch-experiment-spec.v1" and len(spec["cases"]) == 4,
            "epoch modeled input cohort differs")
    require(not args.output.exists(), "epoch flow output must be unused")
    args.output.mkdir(parents=True)
    report = {"schema": "kit.sw2026.sdk-epoch-flow.v1", "passed": False,
              "source_manifest_sha256": args.manifest_sha256,
              "base_source_manifest_sha256": manifest["base_source_manifest_sha256"],
              "spec_sha256": digest((TOOLS / "EpochExperimentSpec01.json").read_bytes()),
              "cases": [], "negative_cases": [], "published_refusals": [], "process_count": 0,
              "hidden_inputs_read": False, "native_acceptance": False, "heldout_acceptance": False,
              "public_drawing_writer_enabled": False, "native_deck_ready_for_review": False}
    result_path = args.output / "Result.json"
    def checkpoint():
        result_path.write_bytes(encode(report))
    checkpoint()
    requests = {}
    try:
        for case in spec["cases"]:
            request = make_epoch_request(spec, case)
            requests[case["name"]] = request
            row = {"name": case["name"], "changed_axis": case["changed_axis"], "builds": [], "passed": False}
            report["cases"].append(row)
            values = []
            for index in range(2):
                record, value = worker("EpochPairProcess.py", request, args.output / (case["name"] + "Build" + str(index)))
                row["builds"].append(record)
                report["process_count"] += 1
                values.append(value)
                checkpoint()
                require(record["return_code"] == 0 and value.get("passed") is True, "guarded epoch factory failed: " + str(value.get("diagnostic")))
            require(values[0] == values[1], "repeated independent clock composition differs")
            build = values[0]
            baseline_record, baseline = worker("OriginPairProcess.py", request["origin_request"], args.output / (case["name"] + "Default"))
            report["process_count"] += 1
            row["default_constructor"] = baseline_record
            checkpoint()
            require(baseline_record["return_code"] == 0 and baseline.get("passed") is True,
                    "unchanged constructor counterpart failed: " + str(baseline.get("diagnostic")))
            row["default_comparison"] = compare_defaults(build, baseline, case["changed_axis"])
            record, prepared = worker("EpochPairPrepare.py", {"request": request, "build": build}, args.output / (case["name"] + "Prepare"))
            report["process_count"] += 1
            row.update(preparation=record, prepared=prepared)
            checkpoint()
            require(record["return_code"] == 0 and prepared.get("passed") is True,
                    "independent epoch preparation failed: " + str(prepared.get("diagnostic")))
            files = {}
            for kind, suffix in (("child", ".SLDPRT"), ("drawing", ".SLDDRW")):
                value = b64decode(build[kind + "_base64"], validate=True)
                path = args.output / (case["name"] + suffix)
                require(len(value) == build[kind + "_bytes"] and digest(value) == build[kind + "_sha256"],
                        "generated clock candidate custody differs")
                write_new(path, value)
                files[kind] = {"path": path.name, "bytes": len(value), "sha256": digest(value)}
            row.update(files=files, clock_plan=request["clock_plan"], profile=build["profile"], passed=True)
            checkpoint()
        for mode, key in (("published-earlier-modified", "EarlierArchiveTime"),
                          ("published-independent-history", "LaterHistoryEvent")):
            record, value = worker("EpochGuardProcess.py", {"mode": mode, "request": requests[key]}, args.output / mode)
            report["process_count"] += 1
            row = {**record, "observed": value, "passed": record["return_code"] == 0 and value.get("passed") is True
                   and value.get("expected_refusal") is True}
            report["published_refusals"].append(row)
            checkpoint()
            require(row["passed"], "published constructor refusal changed")
        for index, (name, request) in enumerate(negative_requests(requests["ClockBaseline"])):
            record, value = worker("EpochPairProcess.py", request, args.output / ("Reject" + str(index)))
            report["process_count"] += 1
            row = {**record, "name": name, "diagnostic": value.get("diagnostic"),
                   "rejected": record["return_code"] != 0 and value.get("passed") is False
                   and "child_base64" not in value and "drawing_base64" not in value
                   and value.get("runtime_input_file_access_attempts") == 0}
            report["negative_cases"].append(row)
            checkpoint()
            require(row["rejected"], "invalid clock experiment was not rejected atomically")
        report["passed"] = len(report["cases"]) == 4 and len(report["negative_cases"]) == 8 and len(report["published_refusals"]) == 2
        report["native_deck_ready_for_review"] = report["passed"]
    except Exception as error:
        report["error"] = {"exception": type(error).__name__, "diagnostic": str(error)}
    verify_source(args.candidate, args.manifest_sha256)
    checkpoint()
    print(json.dumps({"passed": report["passed"], "process_count": report["process_count"],
                      "result_sha256": digest(result_path.read_bytes()), "native_acceptance": False}))
    return 0 if report["passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
