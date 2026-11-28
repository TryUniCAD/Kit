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

from ansi_normalization.Inspect import expected_paths
from ansi_style.JsonDifference import difference


def digest(raw):
    return sha256(raw).hexdigest()


def verify(candidate, expected):
    path = candidate / "SourceManifest.json"
    if digest(path.read_bytes()) != expected:
        raise ValueError("normalization source manifest differs")
    manifest = json.loads(path.read_bytes())
    if (
        ROOT != (candidate / "CodeRoot").resolve()
        or manifest["base_commit"] != "f393c3bdc84a630f82f0b4c52ba67b05967ccaea"
    ):
        raise ValueError("normalization flow is outside its frozen exact base")
    for row in manifest["files"]:
        relative = Path(row["path"])
        source = ROOT / relative
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or source.is_symlink()
            or not source.resolve(strict=True).is_relative_to(ROOT)
        ):
            raise ValueError("normalization source escaped its frozen root")
        raw = source.read_bytes()
        if len(raw) != row["bytes"] or digest(raw) != row["sha256"]:
            raise ValueError("normalization source changed: " + row["path"])
    return manifest


def worker(name, request, prefix):
    raw = json.dumps(
        request, sort_keys=True, ensure_ascii=False, allow_nan=False
    ).encode()
    prefix.with_suffix(".Request.json").write_bytes(raw)
    process = subprocess.run(
        [sys.executable, "-I", "-B", str(TOOLS / name)],
        input=raw,
        capture_output=True,
        cwd=ROOT,
        timeout=180,
    )
    prefix.with_suffix(".stdout.json").write_bytes(process.stdout)
    prefix.with_suffix(".stderr.txt").write_bytes(process.stderr)
    return {
        "returncode": process.returncode,
        "request_sha256": digest(raw),
        "stdout_sha256": digest(process.stdout),
        "stderr_sha256": digest(process.stderr),
    }, json.loads(process.stdout)


def compare(fresh, initialized, places):
    require_equal = (
        "mode",
        "child_shape",
        "profile",
        "text_after",
        "orientation",
        "native_child_path",
        "native_drawing_path",
    )
    if any(fresh[key] != initialized[key] for key in require_equal):
        raise ValueError(
            "initialization changed authored geometry or origin/link ownership"
        )
    result = {}
    expected = expected_paths()
    for name in ("child_details", "drawing_details"):
        rows = difference(
            fresh["presentation"][name], initialized["presentation"][name]
        )
        if {row["path"].removeprefix("/") for row in rows} != expected or len(
            rows
        ) != 81:
            raise ValueError(
                "initialization changed an unpredicted typed presentation field"
            )
        for row in rows:
            path = row["path"]
            if (
                path.startswith("/ff68/")
                and path != "/ff68/f10"
                and row["right"] != places
            ):
                raise ValueError(
                    "precision prediction differs from authored document precision"
                )
        result[name] = rows
    for kind, allowed in (
        ("child", ["Contents/Config-0", "Contents/Config-0-ResolvedFeatures"]),
        ("drawing", ["Contents/Definition"]),
    ):
        left, right = fresh[kind + "_streams"], initialized[kind + "_streams"]
        if set(left) != set(right):
            raise ValueError("initialization changed stream membership")
        changed = [key for key in left if left[key]["sha256"] != right[key]["sha256"]]
        if changed != allowed:
            raise ValueError(
                "initialization changed streams outside actual style ownership"
            )
        result[kind + "_changed_streams"] = changed
    old, new = fresh["linked_state"], initialized["linked_state"]
    if (
        old["resolved_graph"] != new["resolved_graph"]
        or old["seed_classes"] != new["seed_classes"]
    ):
        raise ValueError(
            "normalization changed a resolved field or actual inherited identity"
        )
    if (
        new["config_counter"] - old["config_counter"] != 8
        or new["resolved_counter"] - old["resolved_counter"] != 8
    ):
        raise ValueError(
            "owned dual units did not account for the exact shared map growth"
        )
    before, after = old["seed_objects"], new["seed_objects"]
    added = set(after) - set(before)
    expected_added = {
        "config/fields/fae0/f13b0/" + key + "/ff0/fb8"
        for key in ("fe0", "f2f8", "f3f8", "f500", "f608", "f830", "f960", "fa68")
    }
    if added != expected_added or any(
        key not in after or before[key] != after[key] for key in before
    ):
        raise ValueError(
            "configuration map changed objects outside eight owned dual units"
        )
    result["shared_map_growth"] = {
        "config": 8,
        "resolved": 8,
        "new_owned_dual_paths": sorted(added),
        "complete_resolved_fields_and_aliases_unchanged": True,
        "old_config_counter": old["config_counter"],
        "new_config_counter": new["config_counter"],
        "old_resolved_counter": old["resolved_counter"],
        "new_resolved_counter": new["resolved_counter"],
    }
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--manifest-sha256", required=True)
    args = parser.parse_args()
    verify(args.candidate, args.manifest_sha256)
    requests = json.loads((TOOLS / "AnsiNormalizationRequests01.json").read_bytes())
    args.output.mkdir(parents=True, exist_ok=False)
    report = {
        "schema": "kit.sw2026.ansi-normalization-flow.v1",
        "passed": False,
        "source_manifest_sha256": args.manifest_sha256,
        "cases": [],
        "comparisons": [],
        "rejections": [],
        "native_acceptance": False,
        "heldout_acceptance": False,
        "source_original_admission": False,
        "full_presentation_retention_required": True,
    }
    try:
        for group in requests["cases"]:
            outputs = {}
            for initialization in ("fresh", "document-units"):
                request = dict(group["request"], initialization=initialization)
                label = group["name"] + (
                    "Fresh" if initialization == "fresh" else "Initialized"
                )
                builds = []
                for repeat in range(2):
                    row, result = worker(
                        "AnsiNormalizationProcess.py",
                        request,
                        args.output / (label + "Build" + str(repeat)),
                    )
                    if row["returncode"] != 0 or result.get("passed") is not True:
                        raise ValueError(
                            "guarded initialization failed: "
                            + result.get("diagnostic", "no result")
                        )
                    if (
                        result["runtime_input_file_access_attempts"]
                        or result["sdk_research_imports"]
                    ):
                        raise ValueError(
                            "normalization crossed the runtime input boundary"
                        )
                    builds.append((row, result))
                if builds[0][1] != builds[1][1]:
                    raise ValueError("repeat independently built outputs differ")
                preparation, prepared = worker(
                    "AnsiNormalizationPrepare.py",
                    builds[0][1],
                    args.output / (label + "Prepare"),
                )
                if preparation["returncode"] != 0 or prepared.get("passed") is not True:
                    raise ValueError(
                        "independent initialization replay failed: "
                        + prepared.get("diagnostic", "no result")
                    )
                outputs[initialization] = builds[0][1]
                if initialization == "document-units":
                    for kind, suffix in (("child", ".SLDPRT"), ("drawing", ".SLDDRW")):
                        with (args.output / (label + suffix)).open("xb") as stream:
                            stream.write(
                                b64decode(builds[0][1][kind + "_base64"], validate=True)
                            )
                report["cases"].append(
                    {
                        "name": label,
                        "mode": request["mode"],
                        "initialization": initialization,
                        "precision": group["precision"],
                        "builds": [item[0] for item in builds],
                        "preparation": preparation,
                        "child_sha256": builds[0][1]["child_sha256"],
                        "drawing_sha256": builds[0][1]["drawing_sha256"],
                    }
                )
            report["comparisons"].append(
                {
                    "name": group["name"],
                    **compare(
                        outputs["fresh"], outputs["document-units"], group["precision"]
                    ),
                }
            )
        first = dict(requests["cases"][0]["request"], initialization="document-units")
        for label in (
            "unknown_policy",
            "unknown_mode",
            "nonmetric_part",
            "nonmetric_drawing",
            "empty_part_exclusions",
            "empty_drawing_exclusions",
            "boolean_part_precision",
            "boolean_drawing_precision",
        ):
            request = deepcopy(first)
            if label == "unknown_policy":
                request["initialization"] = "unexplained"
            elif label == "unknown_mode":
                request["mode"] = "unexplained"
            elif label == "nonmetric_part":
                request["origin_request"]["part"]["settings"]["document_units"][
                    "length_unit"
                ] = "in"
            elif label == "nonmetric_drawing":
                request["origin_request"]["native"]["options"]["units"][
                    "length_unit"
                ] = "in"
            elif label == "empty_part_exclusions":
                request["origin_request"]["part"]["settings"]["styles"][
                    "exclusion_names"
                ] = []
            elif label == "empty_drawing_exclusions":
                request["origin_request"]["native"]["options"]["styles"][
                    "exclusion_names"
                ] = []
            elif label == "boolean_part_precision":
                request["origin_request"]["part"]["settings"]["document_units"][
                    "decimal_places"
                ] = True
            else:
                request["origin_request"]["native"]["options"]["units"][
                    "decimal_places"
                ] = True
            row, result = worker(
                "AnsiNormalizationProcess.py", request, args.output / ("Reject" + label)
            )
            if (
                row["returncode"] != 3
                or result.get("passed") is not False
                or result.get("runtime_input_file_access_attempts") != 0
            ):
                raise ValueError(
                    "unsupported initialization request did not refuse atomically"
                )
            report["rejections"].append(
                {"name": label, **row, "diagnostic": result["diagnostic"]}
            )
        report["passed"] = True
    except Exception as error:
        report["diagnostic"] = str(error)
        report["exception"] = type(error).__name__
    verify(args.candidate, args.manifest_sha256)
    with (args.output / "Result.json").open("x", encoding="utf-8") as stream:
        json.dump(
            report,
            stream,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        )
        stream.write("\n")
    print(
        json.dumps(
            {
                "passed": report["passed"],
                "case_variants": len(report["cases"]),
                "comparisons": len(report["comparisons"]),
                "rejections": len(report["rejections"]),
            }
        )
    )
    return 0 if report["passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
