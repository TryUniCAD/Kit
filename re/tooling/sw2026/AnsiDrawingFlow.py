from __future__ import annotations

import sys
from pathlib import Path, PureWindowsPath

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
from ansi_style.JsonDifference import difference
from interchange.serialization.EncodeData import ToData
from interchange.serialization.Deserialize import FromData


def digest(raw):
    return sha256(raw).hexdigest()


def write(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(
            value, stream, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False
        )
        stream.write("\n")


def verify(candidate, expected):
    path = candidate / "SourceManifest.json"
    if digest(path.read_bytes()) != expected:
        raise ValueError("ANSI pair manifest differs")
    value = json.loads(path.read_bytes())
    if (
        ROOT != (candidate / "CodeRoot").resolve()
        or value["base_commit"] != "ebe51e167c0cc43b28fbca94033b7122d2042004"
    ):
        raise ValueError("ANSI pair flow is outside its frozen exact base")
    for row in value["files"]:
        relative = Path(row["path"])
        source = ROOT / relative
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or source.is_symlink()
            or not source.resolve(strict=True).is_relative_to(ROOT)
        ):
            raise ValueError("ANSI pair source escapes its root")
        raw = source.read_bytes()
        if len(raw) != row["bytes"] or digest(raw) != row["sha256"]:
            raise ValueError("ANSI pair source changed: " + row["path"])
    return value


def worker(name, request, prefix):
    encoded = json.dumps(
        request, sort_keys=True, ensure_ascii=False, allow_nan=False
    ).encode()
    prefix.with_suffix(".Request.json").write_bytes(encoded)
    completed = subprocess.run(
        [sys.executable, "-I", "-B", str(TOOLS / name)],
        input=encoded,
        capture_output=True,
        cwd=ROOT,
        timeout=180,
    )
    prefix.with_suffix(".stdout.json").write_bytes(completed.stdout)
    prefix.with_suffix(".stderr.txt").write_bytes(completed.stderr)
    result = json.loads(completed.stdout)
    return {
        "returncode": completed.returncode,
        "request_sha256": digest(encoded),
        "stdout_sha256": digest(completed.stdout),
        "stderr_sha256": digest(completed.stderr),
    }, result


def request_for(base, mode, lane):
    job = deepcopy(base)
    code, ui = (0, "moANSI_c") if mode == "ansi" else (1, "moISO_c")
    job["part"]["settings"]["styles"]["standard"] = job["native"]["options"]["styles"][
        "standard"
    ] = code
    job["part"]["settings"]["definition"]["drafting_standard"] = job["native"]["ui"][
        "drafting_standard"
    ] = ui
    folder = (
        PureWindowsPath("C:/KitAnsiDetails01")
        / base["native"]["options"]["name"]
        / lane
    )
    old_child = PureWindowsPath(job["part"]["settings"]["output"]["path_name"])
    old_draw = PureWindowsPath(job["native"]["output"]["path_name"])
    child, drawing = str(folder / old_child.name), str(folder / old_draw.name)
    job["part"]["settings"]["output"]["path_name"] = child
    job["native"]["output"]["path_name"] = drawing
    document = FromData(job["drawing_document"])
    job["drawing_document"] = ToData(
        replace(document, ModelRefs=(replace(document.ModelRefs[0], SourcePath=child),))
    )
    return {
        "schema": "kit.sw2026.ansi-drawing-request.v1",
        "mode": mode,
        "origin_request": job,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--manifest-sha256", required=True)
    args = parser.parse_args()
    manifest = verify(args.candidate, args.manifest_sha256)
    args.output.mkdir(parents=True, exist_ok=False)
    report = {
        "schema": "kit.sw2026.ansi-pair-flow.v1",
        "source_manifest_sha256": args.manifest_sha256,
        "cases": [],
        "comparisons": [],
        "rejections": [],
        "passed": False,
        "native_acceptance": False,
        "heldout_acceptance": False,
        "source_original_admission": False,
    }
    designs = (
        (
            "AnsiDetailCornerAlpha",
            0.041927,
            0.027613,
            0.009173,
            "*Front",
            0.893,
            (0.11917, 0.09137),
            "corner-anchored",
        ),
        (
            "AnsiDetailCenteredBetaΩ",
            0.053219,
            0.031871,
            0.007349,
            "*Top",
            1.071,
            (0.13371, 0.09913),
            "center-anchored",
        ),
    )
    try:
        first = None
        for design in designs:
            base = make_job(*design)
            for scope in ("Compare", "Native"):
                results = {}
                for mode in ("iso", "ansi"):
                    request = request_for(
                        base, mode, scope if scope == "Compare" else mode.upper()
                    )
                    label = design[0] + scope + mode.title()
                    first = first or request
                    builds = []
                    for repeat in range(2):
                        row, result = worker(
                            "AnsiDrawingProcess.py",
                            request,
                            args.output / (label + "Build" + str(repeat)),
                        )
                        if row["returncode"] != 0 or result.get("passed") is not True:
                            raise ValueError(
                                "guarded ANSI pair failed: "
                                + result.get("diagnostic", "no result")
                            )
                        builds.append((row, result))
                    if builds[0][1] != builds[1][1]:
                        raise ValueError("independent ANSI pair builds differ")
                    prep, prepared = worker(
                        "AnsiDrawingPrepare.py",
                        builds[0][1],
                        args.output / (label + "Prepare"),
                    )
                    if prep["returncode"] != 0 or prepared.get("passed") is not True:
                        raise ValueError(
                            "independent ANSI readback failed: "
                            + prepared.get("diagnostic", "no result")
                        )
                    result = builds[0][1]
                    if (
                        result["runtime_input_file_access_attempts"]
                        or result["sdk_research_imports"]
                    ):
                        raise ValueError("ANSI construction input boundary differs")
                    for name, suffix in (("child", ".SLDPRT"), ("drawing", ".SLDDRW")):
                        raw = b64decode(result[name + "_base64"], validate=True)
                        with (args.output / (label + suffix)).open("xb") as stream:
                            stream.write(raw)
                    report["cases"].append(
                        {
                            "name": label,
                            "scope": scope,
                            "design": list(design),
                            "mode": mode,
                            "request_file": label + "Build0.Request.json",
                            "result_file": label + "Build0.stdout.json",
                            "builds": [item[0] for item in builds],
                            "preparation": prep,
                            "child_sha256": result["child_sha256"],
                            "drawing_sha256": result["drawing_sha256"],
                            "paths": {
                                "child": result["native_child_path"],
                                "drawing": result["native_drawing_path"],
                            },
                        }
                    )
                    results[mode] = result
                iso, ansi = results["iso"], results["ansi"]
                if (
                    iso["child_shape"] != ansi["child_shape"]
                    or iso["profile"] != ansi["profile"]
                    or iso["text_after"] != ansi["text_after"]
                ):
                    raise ValueError(
                        "ANSI changed actual geometry dimensions IDs or origin owners"
                    )
                change = {
                    "name": design[0],
                    "scope": scope,
                    "child_details": difference(
                        iso["presentation"]["child_details"],
                        ansi["presentation"]["child_details"],
                    ),
                    "drawing_details": difference(
                        iso["presentation"]["drawing_details"],
                        ansi["presentation"]["drawing_details"],
                    ),
                    "ui_owners": difference(iso["presentation"], ansi["presentation"]),
                }
                for kind in ("child", "drawing"):
                    left, right = iso[kind + "_streams"], ansi[kind + "_streams"]
                    if set(left) != set(right):
                        raise ValueError("ANSI changed the logical stream membership")
                    changed = [
                        key
                        for key in left
                        if left[key]["sha256"] != right[key]["sha256"]
                    ]
                    change[kind + "_changed_streams"] = changed
                    if scope == "Compare" and changed != (
                        ["Contents/Config-0", "Contents/Definition"]
                        if kind == "child"
                        else ["Contents/Definition"]
                    ):
                        raise ValueError(
                            "same-path ANSI changed streams outside actual style and UI owners"
                        )
                if (
                    len(change["child_details"]) != 173
                    or len(change["drawing_details"]) != 173
                ):
                    raise ValueError(
                        "full-pair ANSI differs from the pinned complete default operation"
                    )
                report["comparisons"].append(change)
        for label in (
            "unknown_mode",
            "part_style",
            "drawing_style",
            "part_ui",
            "drawing_ui",
            "boolean_style",
        ):
            request = deepcopy(first)
            if label == "unknown_mode":
                request["mode"] = "unknown"
            elif label == "part_style":
                request["origin_request"]["part"]["settings"]["styles"]["standard"] = 0
            elif label == "drawing_style":
                request["origin_request"]["native"]["options"]["styles"]["standard"] = 0
            elif label == "part_ui":
                request["origin_request"]["part"]["settings"]["definition"][
                    "drafting_standard"
                ] = "moANSI_c"
            elif label == "drawing_ui":
                request["origin_request"]["native"]["ui"][
                    "drafting_standard"
                ] = "moANSI_c"
            else:
                request["origin_request"]["part"]["settings"]["styles"][
                    "standard"
                ] = True
            row, result = worker(
                "AnsiDrawingProcess.py", request, args.output / ("Reject" + label)
            )
            if (
                row["returncode"] != 3
                or result.get("passed") is not False
                or result.get("runtime_input_file_access_attempts") != 0
            ):
                raise ValueError("inconsistent ANSI request did not refuse atomically")
            report["rejections"].append(
                {"case": label, **row, "diagnostic": result["diagnostic"]}
            )
        report["passed"] = True
    except Exception as error:
        report["diagnostic"] = str(error)
        report["exception"] = type(error).__name__
    verify(args.candidate, args.manifest_sha256)
    write(args.output / "Result.json", report)
    print(
        json.dumps(
            {
                "passed": report["passed"],
                "cases": len(report["cases"]),
                "comparisons": len(report["comparisons"]),
                "rejections": len(report["rejections"]),
            }
        )
    )
    return 0 if report["passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
