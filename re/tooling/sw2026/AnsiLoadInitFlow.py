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
import json

from AnsiNormalizationFlow import digest, verify, worker
from ansi_style.JsonDifference import difference


def require(value, diagnostic):
    if not value:
        raise ValueError(diagnostic)


def build(name, request, prefix):
    custody, result = worker(name, request, prefix)
    require(
        custody["returncode"] == 0
        and result.get("passed") is True
        and result.get("runtime_input_file_access_attempts") == 0
        and result.get("sdk_research_imports") == [],
        "guarded drawing load build failed: " + result.get("diagnostic", "no result"),
    )
    return custody, result


def prepare(result, prefix):
    custody, observed = worker("AnsiLoadInitPrepare.py", result, prefix)
    require(
        custody["returncode"] == 0 and observed.get("passed") is True,
        "independent full linked load preparation failed: "
        + observed.get("diagnostic", "no result"),
    )
    require(
        observed["presentation"] == result["presentation"]
        and observed["linked_state"] == result["linked_state"]
        and observed["full_presentation_retention_required"] is True,
        "independent complete style or actual linked graph differs",
    )
    return custody


def unchanged_pair(left, right):
    for key in (
        "child_base64",
        "drawing_base64",
        "child_streams",
        "drawing_streams",
        "presentation",
        "linked_state",
        "child_shape",
        "profile",
        "text_after",
        "orientation",
        "native_child_path",
        "native_drawing_path",
    ):
        require(left[key] == right[key], "constructor comparison changed " + key)


def compare(left, right, mode):
    for key in (
        "child_base64",
        "child_streams",
        "linked_state",
        "child_shape",
        "profile",
        "text_after",
        "orientation",
        "native_child_path",
        "native_drawing_path",
    ):
        require(left[key] == right[key], "load initialization changed " + key)
    expected = []
    if mode == "ansi":
        before = left["presentation"]["drawing_details"]["f20"]
        expected = [
            {"path": "/drawing_details/f20", "left": before, "right": before | 0x100000}
        ]
    rows = difference(left["presentation"], right["presentation"])
    require(rows == expected, "complete presentation changed outside its one-mask rule")
    before_streams, after_streams = left["drawing_streams"], right["drawing_streams"]
    require(set(before_streams) == set(after_streams), "drawing stream set changed")
    changed = [
        key for key in before_streams if before_streams[key] != after_streams[key]
    ]
    require(
        changed == (["Contents/Definition"] if mode == "ansi" else []),
        "load initialization changed an unrelated logical stream",
    )
    if mode == "iso":
        require(
            left["drawing_base64"] == right["drawing_base64"],
            "ISO output bytes changed",
        )
    return {
        "mode": mode,
        "complete_presentation_differences": rows,
        "changed_drawing_streams": changed,
        "child_container_and_all_streams_identical": True,
        "complete_child_linked_fields_and_aliases_identical": True,
        "iso_container_identical": mode == "iso",
        "full_presentation_retention_required": True,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--manifest-sha256", required=True)
    args = parser.parse_args()
    verify(args.candidate, args.manifest_sha256)
    requests = json.loads((TOOLS / "AnsiLoadInitRequests01.json").read_bytes())
    require(
        requests["schema"] == "kit.sw2026.ansi-load-authored-inputs.v1",
        "input contract differs",
    )
    args.output.mkdir(parents=True, exist_ok=False)
    report = {
        "schema": "kit.sw2026.ansi-load-flow.v1",
        "passed": False,
        "source_manifest_sha256": args.manifest_sha256,
        "cases": [],
        "comparisons": [],
        "explicit_true_cases": [],
        "rejections": [],
        "process_count": 0,
        "native_acceptance": False,
        "heldout_acceptance": False,
        "source_original_admission": False,
        "public_drawing_writer_changed": False,
        "full_presentation_retention_required": True,
    }
    reference = {}
    try:
        for group in requests["cases"]:
            name = group["name"]
            request = deepcopy(group["request"])
            legacy = {
                key: value for key, value in request.items() if key != "drawing_load"
            }
            legacy["schema"] = "kit.sw2026.ansi-normalization-request.v1"
            old_custody, old = build(
                "AnsiNormalizationProcess.py", legacy, args.output / (name + "Prior")
            )
            control_request = deepcopy(request)
            control_request["drawing_load"]["policy"] = "constructor"
            control_custody, control = build(
                "AnsiLoadInitProcess.py",
                control_request,
                args.output / (name + "Constructor"),
            )
            unchanged_pair(old, control)
            control_preparation = prepare(
                control, args.output / (name + "ConstructorPrepare")
            )
            repeats = []
            for repeat in range(2):
                repeats.append(
                    build(
                        "AnsiLoadInitProcess.py",
                        request,
                        args.output / (name + "Load" + str(repeat)),
                    )
                )
            require(
                repeats[0][1] == repeats[1][1],
                "repeat load-initialized construction differs",
            )
            loaded = repeats[0][1]
            prepared = prepare(loaded, args.output / (name + "LoadPrepare"))
            report["process_count"] += 6
            prediction = compare(control, loaded, request["mode"])
            for kind, suffix in (("child", ".SLDPRT"), ("drawing", ".SLDDRW")):
                with (args.output / (name + suffix)).open("xb") as stream:
                    stream.write(b64decode(loaded[kind + "_base64"], validate=True))
            report["cases"].append(
                {
                    "name": name,
                    "mode": request["mode"],
                    "prior_build": old_custody,
                    "constructor_build": control_custody,
                    "constructor_preparation": control_preparation,
                    "load_builds": [item[0] for item in repeats],
                    "load_preparation": prepared,
                    "child_sha256": loaded["child_sha256"],
                    "child_bytes": loaded["child_bytes"],
                    "drawing_sha256": loaded["drawing_sha256"],
                    "drawing_bytes": loaded["drawing_bytes"],
                    "drawing_load_operation": loaded["drawing_load_operation"],
                    "exact_prior_constructor_output": True,
                }
            )
            report["comparisons"].append({"name": name, **prediction})
            reference.setdefault(request["mode"], (request, loaded))
        for mode, (request, loaded) in reference.items():
            authored = deepcopy(request)
            authored["drawing_load"]["explicit_centerline"] = True
            custody, actual = build(
                "AnsiLoadInitProcess.py",
                authored,
                args.output / ("ExplicitTrue" + mode),
            )
            unchanged_pair(actual, loaded)
            report["process_count"] += 1
            report["explicit_true_cases"].append(
                {"mode": mode, **custody, "same_complete_pair": True}
            )
        for label in (
            "false_ansi",
            "false_iso",
            "integer_intent_zero",
            "integer_intent_one",
            "boolean_version",
            "future_version",
            "unknown_policy",
            "extra_override_request",
        ):
            request = deepcopy(reference["ansi"][0])
            if label == "false_iso":
                request = deepcopy(reference["iso"][0])
            if label.startswith("false_"):
                request["drawing_load"]["explicit_centerline"] = False
            elif label == "integer_intent_zero":
                request["drawing_load"]["explicit_centerline"] = 0
            elif label == "integer_intent_one":
                request["drawing_load"]["explicit_centerline"] = 1
            elif label == "boolean_version":
                request["drawing_load"]["file_version"] = True
            elif label == "future_version":
                request["drawing_load"]["file_version"] = 19001
            elif label == "unknown_policy":
                request["drawing_load"]["policy"] = "unexplained"
            else:
                request["drawing_load"]["override"] = "unproved-owner"
            custody, refused = worker(
                "AnsiLoadInitProcess.py", request, args.output / ("Reject" + label)
            )
            report["process_count"] += 1
            require(
                custody["returncode"] == 3
                and refused.get("passed") is False
                and refused.get("runtime_input_file_access_attempts") == 0
                and "child_base64" not in refused
                and "drawing_base64" not in refused,
                "conflicting or unsupported initialization did not refuse atomically",
            )
            report["rejections"].append(
                {"name": label, **custody, "diagnostic": refused["diagnostic"]}
            )
        report["passed"] = True
    except Exception as error:
        report["exception"] = type(error).__name__
        report["diagnostic"] = str(error)
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
                "process_count": report["process_count"],
                "cases": len(report["cases"]),
                "rejections": len(report["rejections"]),
            }
        )
    )
    return 0 if report["passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
