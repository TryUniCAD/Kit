from __future__ import annotations

import argparse
from base64 import b64decode
from copy import deepcopy
import json
from math import isfinite
from pathlib import Path, PureWindowsPath
from shutil import copyfile
import subprocess
import sys


SOURCE_MANIFEST_SHA256 = "c1e8e5788d32e9fbdfdae83b1ec95410835b2ee05c47a2a278dfc2ad88ae1de4"
RESEARCH_ROOT = Path(__file__).resolve().parents[3]
RESEARCH_TOOLS = Path(__file__).resolve().parent


def bootstrap_writer():
    from hashlib import sha256

    def argument(name):
        return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else None

    root = argument("--writer-root")
    if root is not None:
        writer = Path(root).resolve()
        manifest = Path(argument("--writer-sources"))
        expected = argument("--writer-sources-sha256")
    elif len(sys.argv) > 1 and sys.argv[1] == "attach-comparison":
        directory = Path(argument("--output"))
        data = (directory / "HostPreparation.json").read_bytes()
        if sha256(data).hexdigest() != argument("--host-preparation-sha256"):
            raise ValueError("blind generation freeze differs before SDK initialization")
        host = json.loads(data)
        writer = Path(host["writer_root"])
        manifest = directory / "GeneratorSourceSnapshot.json"
        expected = host["writer_source_snapshot_sha256"]
    else:
        raise ValueError("the immutable writer root and source manifest must be explicit")
    data = manifest.read_bytes()
    if expected != SOURCE_MANIFEST_SHA256 or sha256(data).hexdigest() != expected:
        raise ValueError("the qualified immutable drawing source manifest differs")
    source = json.loads(data)
    if len(source["files"]) != 3685:
        raise ValueError("the qualified drawing source closure is incomplete")
    for name, expected_hash in source["files"].items():
        if sha256((writer / name).read_bytes()).hexdigest() != expected_hash:
            raise ValueError(f"immutable drawing dependency changed before SDK initialization: {name}")
    sys.path[:0] = [str(writer / "re/tooling/sw2026"), str(writer / "re/tooling/sw2026/serial"), str(writer / "src"), str(writer)]
    return writer


FROZEN_WRITER = bootstrap_writer()

from PrepareScaledDrawing import (
    canonical_rotation, checked_json, digest, encoded, file_summary,
    rotate, verify_prediction, write_json,
)
from InspectBlindDrawing import HELDOUT_NAMES, ORIGINAL_LOCK, ORIGINAL_SPECS, SCHEMA, TOOL_NAMES
from InspectScaledDrawing import ORACLE_SHA256, ORIENTATIONS, relative_file
from BlindDrawingSemantics import compare_values
from CheckDrawingDefinitions import checked_artifacts


ROOT, TOOLS = RESEARCH_ROOT, RESEARCH_TOOLS
NEW_METHOD_FILES = frozenset(("PrepareBlindDrawing.py", "InspectBlindDrawing.py", "BlindDrawingSemantics.py"))

HOST_SCHEMA = "kit.sw2026.blind-standard-drawing-host-preparation.v1"
BINDING_SCHEMA = "kit.sw2026.blind-drawing-neutral-binding.v1"
PROFILE_SCHEMA = "kit.sw2026.generated-scaled-drawing-native-result.v1"
DISCLOSED_SPECS = {
    "72d46ec33a13b1d5074e053e4052d31afa82ab575c395affcea8d9c247973b73": ORIGINAL_LOCK,
    "acb78b422358773320a6601d38bef8e17107f268e8912574d1c23a558584a03c": "99c3e345182c20853445bd7240a881d6fce22d397961779445961d61718a3298",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def registration(arguments):
    names = tuple(arguments.case)
    require(names and len(names) == len(set(names)), "blind case selection must be nonempty and unique")
    if arguments.disclosed:
        require(DISCLOSED_SPECS.get(arguments.specs_sha256) == arguments.source_lock_sha256,
                "disclosed mode requires an existing public drawing specification and lock")
    else:
        require(arguments.specs_sha256 == ORIGINAL_SPECS and arguments.source_lock_sha256 == ORIGINAL_LOCK
                and set(names) <= set(HELDOUT_NAMES), "held-out mode requires the original registered specification and H01/H02 slots")
    lock = checked_json(arguments.source_lock, arguments.source_lock_sha256)
    require(lock["passed"] and lock["pinned_inputs_immutable"] and lock["control_results"] == [True, True]
            and lock["oracle_sha256"] == ORACLE_SHA256, "registered native drawing source lock is unqualified")
    split = "discovery" if arguments.disclosed else "heldout"
    registered = {case["name"] for case in lock["cases"] if case["split"] == split}
    require(set(names) <= registered and (arguments.disclosed or registered == set(HELDOUT_NAMES)), "source slot registration differs")
    return lock


def discovery_profile(arguments):
    writer = arguments.writer_root.resolve()
    require(writer != ROOT and not writer.is_relative_to(ROOT), "blind writer requires its immutable private source closure")
    source = checked_json(arguments.writer_sources, arguments.writer_sources_sha256)
    for name, expected in source["files"].items():
        require(digest((writer / name).read_bytes()) == expected, f"frozen drawing writer source changed: {name}")
    if arguments.profile_result is None:
        require(arguments.disclosed, "held-out specification stays sealed until a qualified discovery profile is bound")
        return False
    result = checked_json(arguments.profile_result, arguments.profile_result_sha256)
    require(result["schema"] == PROFILE_SCHEMA and result["scaled_drawing_trial_passed"] and result["controls_healthy"]
            and result["distinct_processes"] == result["phase_count"] == 12 and result["input_files_immutable"],
            "scaled standard-view native discovery profile did not pass")
    require(arguments.writer_sources_sha256 == arguments.profile_sources_sha256
            and checked_json(arguments.profile_sources, arguments.profile_sources_sha256) == source,
            "qualified discovery and immutable writer closures differ")
    return True


def method_source(name):
    return TOOLS / name if name in NEW_METHOD_FILES else FROZEN_WRITER / "re/tooling/sw2026" / name


def method_snapshot():
    names = {*TOOL_NAMES, "PrepareBlindDrawing.py", "PrepareScaledDrawing.py", "serial/CheckDrawingDefinitions.py"}
    return {"schema": "kit.sw2026.blind-drawing-method-source-snapshot.v1",
            "files": {name: digest(method_source(name).read_bytes()) for name in sorted(names)}}


def generate_pair(request, writer_root):
    data = encoded(request)
    command = [sys.executable, "-B", str(writer_root / "re/tooling/sw2026/DrawingFrontBundleProcess.py")]
    outcomes = [subprocess.run(command, cwd=writer_root, input=data, capture_output=True, timeout=90) for _ in range(2)]
    for outcome in outcomes:
        require(outcome.returncode == 0, outcome.stderr.decode("utf-8", errors="replace"))
    require(outcomes[0].stdout == outcomes[1].stdout, "immutable blind writer replay differs")
    report = json.loads(outcomes[0].stdout)
    require(report["native_acceptance"] is False and report["input_runtime_file_access_attempts"] == 0
            and report["inspection"]["readback_exact"] and report["inspection"]["detailing_bucket_count"] == 0,
            "immutable blind writer graph proof failed")
    artifacts = {}
    for kind in ("drawing", "part"):
        payload = b64decode(report[kind].pop("artifact_base64"), validate=True)
        require(digest(payload) == report[kind]["sha256"] and len(payload) == report[kind]["bytes"],
                "immutable blind writer artifact differs from its report")
        artifacts[kind] = payload
    return report, artifacts, {"twice_identical": True, "guarded_build_count": 2,
        "stdout_sha256": digest(outcomes[0].stdout), "runtime_input_file_access_attempts": 0}


def binding(arguments):
    value = checked_json(arguments.neutral_binding, arguments.neutral_binding_sha256)
    require(value["schema"] == BINDING_SCHEMA and value["source_lock_sha256"] == ORIGINAL_LOCK
            and value["source_child_sha256"] == "4f752c0093f04a3a383b68bfaeaad8b0fc05285d064989d818c3dc92d990a1ce"
            and value["neutral_inputs_complete"] is True and value["annotation_intent"] == "none",
            "complete independent child, sheet, naming and annotation intent must be bound before unseal")
    require(set(value["authorities"]) == {"part", "sheet", "names", "presentation", "provenance"}
            and all(row["kind"] in ("independent-author-input", "source-proven-rule", "disclosed-common-template-intent")
                    and row["references"] for row in value["authorities"].values()), "neutral input authority is incomplete")
    request = value["request"]
    require(set(request) == {"drawing", "part", "view"} and request["drawing"]["sheet"]["paper_size"] == "ansi-a-landscape",
            "neutral binding requires a complete admitted bundle")
    require(all("saved_at" in request[key]["output"] for key in ("drawing", "part")), "neutral binding needs explicit save times")
    return value


def admission(case):
    view = case["view"]
    if view is None:
        return ["a model view is required; blank-sheet coverage remains separate"]
    require(isinstance(view, dict) and set(view) == {"orientation", "position_m", "scale"}, "source view schema differs")
    require(isinstance(view["position_m"], list) and len(view["position_m"]) == 2
            and all(type(value) in (int, float) and isfinite(value) and value > 0 for value in view["position_m"]),
            "source position requires two finite positive numbers")
    reasons = []
    if view["orientation"] not in ORIENTATIONS:
        reasons.append("standard orientation is outside the frozen named-view grammar")
    scale = view["scale"]
    if type(scale) not in (int, float) or not isfinite(scale) or scale <= 0 or not isfinite(1.0 / scale):
        reasons.append("explicit scale must be finite, positive and have a finite inverse")
    return reasons


def request_for(base, case, windows_root):
    request = deepcopy(base)
    request["drawing"]["name"] = case["name"]
    view = case["view"]
    request["view"].update(orientation=view["orientation"], position=list(view["position_m"]), scale=view["scale"])
    directory = windows_root / "GeneratedInputs" / case["name"]
    for kind, suffix, stem in (("drawing", ".SLDDRW", case["name"]),
                               ("part", ".SLDPRT", request["part"]["document"]["name"])):
        require(PureWindowsPath(stem).name == stem and stem not in (".", ".."), "neutral document name is not a single component")
        request[kind]["output"]["path_name"] = str(directory / (stem + suffix))
    return request


def predict(request):
    from itertools import product
    from PrepareScaledDrawing import prediction

    view = request["view"]
    scaled = deepcopy(request)
    scaled["view"]["scale"] = 1.0
    scaled["view"]["position"] = [0.1397, 0.10795]
    result = prediction(scaled)
    document = request["part"]["document"]
    xs, ys = zip(*document["vertices_m"], strict=True)
    corners = list(product((min(xs), max(xs)), (min(ys), max(ys)), (0.0, document["depth_m"])))
    center = result["expected"]["view"]["child_center_m"]
    rotation = canonical_rotation(view["orientation"])
    scale = view["scale"]
    effective = 1.0 if abs(scale - 1.0) <= 1e-8 else scale
    position = [*view["position"], 0.0]
    dimensions = result["expected"]["sheet_properties"][5:7]
    require(all(0 < value < size for value, size in zip(position[:2], dimensions, strict=True)), "source view centre lies outside its authored sheet")
    translation = [value - effective * coordinate for value, coordinate in zip(position, rotate(rotation, center), strict=True)]
    projected = [[effective * coordinate + offset for coordinate, offset in zip(rotate(rotation, corner), translation, strict=True)] for corner in corners]
    require(all(isfinite(value) for corner in projected for value in corner), "projected view geometry overflows its finite coordinate domain")
    raw = [min(point[0] for point in projected), min(point[1] for point in projected), max(point[0] for point in projected), max(point[1] for point in projected)]
    margin = result["border_margin_m"]
    result["expected"]["view"].update(position_m=list(view["position"]), scale=scale,
        model_to_view=[*rotation, *translation, float(scale), 0.0, 0.0, 0.0],
        outline_m=[value + offset for value, offset in zip(raw, (-margin, -margin, margin, margin), strict=True)])
    result.update(model_corners_m=corners, projected_corners_m=projected, raw_outline_m=raw, independent_preflight_passed=False)
    return result


def generate_host(arguments):
    lock = registration(arguments)
    qualified = discovery_profile(arguments)
    neutral = binding(arguments)
    output = arguments.output.resolve()
    require(not output.exists() and not output.is_relative_to(ROOT), "choose an unused blind-generation directory outside the checkout")
    windows = PureWindowsPath(arguments.windows_directory)
    require(windows.is_absolute(), "blind generation needs an absolute encoded Windows directory")
    specs = checked_json(arguments.specs, arguments.specs_sha256)
    require(specs["schema"] == "kit.sw2026.drawing-source-specs.v1", "original source recipe schema differs")
    selected = [case for case in specs["cases"] if case["name"] in arguments.case]
    require(len(selected) == len(arguments.case) and len({case["name"] for case in selected}) == len(selected)
            and all(case["split"] == ("discovery" if arguments.disclosed else "heldout") for case in selected), "original source recipe selection differs")
    sources = checked_json(arguments.writer_sources, arguments.writer_sources_sha256)
    method = method_snapshot()
    output.mkdir(parents=True, exist_ok=False)
    (output / "NeutralBinding.json").write_bytes(arguments.neutral_binding.read_bytes())
    (output / "SourceLock.json").write_bytes(arguments.source_lock.read_bytes())
    write_json(output / "GeneratorSourceSnapshot.json", sources)
    write_json(output / "MethodSourceSnapshot.json", method)
    report = {"schema": HOST_SCHEMA, "mode": "disclosed" if arguments.disclosed else "heldout", "cases": [],
              "source_specs_sha256": arguments.specs_sha256, "source_lock_sha256": arguments.source_lock_sha256,
              "neutral_binding_sha256": arguments.neutral_binding_sha256, "writer_source_snapshot_sha256": digest(encoded(sources)),
              "mapper_sha256": digest(Path(__file__).read_bytes()), "writer_discovery_profile_qualified": qualified,
              "writer_root": str(arguments.writer_root.resolve()),
              "author_observations_read": False, "native_source_payloads_read": False, "vendor_runtime_executed": False,
              "writer_output_count": 0, "native_acceptance": False, "source_artifacts": {}}
    for case in selected:
        row = {"name": case["name"], "state": "unsupported_before_oracle", "writer_output_count": 0, "reasons": admission(case)}
        report["cases"].append(row)
        if row["reasons"]:
            continue
        request = request_for(neutral["request"], case, windows)
        prediction = predict(request)
        built, artifacts, checks = generate_pair(request, arguments.writer_root.resolve())
        verify_prediction(built, prediction)
        folder = output / "Cases" / case["name"]
        folder.mkdir(parents=True, exist_ok=False)
        for name, value in (("NeutralRequest.json", request), ("Construction.json", built), ("Prediction.json", prediction), ("BuildChecks.json", checks)):
            target = folder / name
            write_json(target, value)
            report["source_artifacts"][str(target.relative_to(output))] = digest(target.read_bytes())
        destination = output / "GeneratedInputs" / case["name"]
        destination.mkdir(parents=True, exist_ok=False)
        row.update(state="admitted_host_generated", writer_output_count=2, expected=prediction["expected"], tree=prediction["tree"],
                   directory=str(destination.relative_to(output)), kind="neutral-generated")
        for kind, data in artifacts.items():
            filename = PureWindowsPath(request[kind]["output"]["path_name"]).name
            (destination / filename).write_bytes(data)
            row[kind] = file_summary(filename, data)
        report["writer_output_count"] += 2
    discovery_profile(arguments)
    require(method_snapshot() == method, "blind mapper or observer source changed during construction")
    require(digest(arguments.specs.read_bytes()) == arguments.specs_sha256
            and digest(arguments.neutral_binding.read_bytes()) == arguments.neutral_binding_sha256, "blind neutral source changed")
    report.update(writer_sources_immutable=True, neutral_inputs_immutable=True)
    for name in ("NeutralBinding.json", "SourceLock.json", "GeneratorSourceSnapshot.json", "MethodSourceSnapshot.json"):
        report["source_artifacts"][name] = digest((output / name).read_bytes())
    if arguments.profile_result is not None:
        for name, source in (("DiscoveryProfile.json", arguments.profile_result), ("DiscoveryProfileSources.json", arguments.profile_sources)):
            copyfile(source, output / name)
            report["source_artifacts"][name] = digest((output / name).read_bytes())
    write_json(output / "HostPreparation.json", report)
    return {"output": str(output), "host_preparation_sha256": digest((output / "HostPreparation.json").read_bytes()),
            "writer_output_count": report["writer_output_count"], "author_observations_read": False,
            "native_source_payloads_read": False, "vendor_runtime_executed": False}


def source_pair(corpus, lock, name, output, directory):
    case, = [row for row in lock["cases"] if row["name"] == name]
    native, observed, _ = checked_artifacts(corpus, case)
    child = (corpus / name / "author/GeneratedChildFile.SLDPRT").read_bytes()
    require(digest(child) == case["reference_part_sha256"] == lock["reference_part_sha256"], "comparison source child differs from the original lock")
    destination = output / directory
    destination.mkdir(parents=True, exist_ok=False)
    filename = name + ".SLDDRW"
    (destination / filename).write_bytes(native)
    (destination / "GeneratedChildFile.SLDPRT").write_bytes(child)
    return {"name": name, "directory": directory, "kind": "native-pristine", "source_case": name, "expected": observed,
            "drawing": file_summary(filename, native), "part": file_summary("GeneratedChildFile.SLDPRT", child),
            "source_record_sha256": case["record_sha256"]}


def attach_comparison(arguments):
    output = arguments.output.resolve()
    require(not (output / "Trial.json").exists(), "blind comparison packet already exists")
    host = checked_json(output / "HostPreparation.json", arguments.host_preparation_sha256)
    require(host["schema"] == HOST_SCHEMA and not host["author_observations_read"] and not host["native_source_payloads_read"]
            and host["writer_sources_immutable"] and host["neutral_inputs_immutable"], "blind generation was not independently frozen")
    for name, expected in host["source_artifacts"].items():
        require(digest(relative_file(output, name).read_bytes()) == expected, f"frozen blind generation artifact changed: {name}")
    frozen = json.loads((output / "GeneratorSourceSnapshot.json").read_bytes())
    for name, expected in frozen["files"].items():
        require(digest((Path(host["writer_root"]) / name).read_bytes()) == expected, f"blind writer changed before comparison attachment: {name}")
    require(method_snapshot() == json.loads((output / "MethodSourceSnapshot.json").read_bytes()),
            "blind method changed before comparison attachment")
    lock = checked_json(output / "SourceLock.json", host["source_lock_sha256"])
    corpus = arguments.corpus.resolve()
    control_name = "D01FrontView" if host["source_lock_sha256"] == ORIGINAL_LOCK else "D00ScaledFront"
    control = source_pair(corpus, lock, control_name, output, "NativeInputs/Control")
    cases = []
    preflight = []
    for generated in host["cases"]:
        if generated["state"] == "unsupported_before_oracle":
            cases.append(generated)
            continue
        name = generated["name"]
        source = source_pair(corpus, lock, name, output, "NativeInputs/" + name)
        actual, expected = source["expected"], generated["expected"]
        comparable = {"sheet": actual["sheet"], "sheet_properties": actual["sheet_properties"], "whats_wrong": actual["whats_wrong"],
                      "view": {key: actual["view"][key] for key in expected["view"]}}
        compared = compare_values(comparable, expected)
        preflight.append({"name": name, **compared})
        cases.append({"name": name, "state": generated["state"], "writer_output_count": 2, "source": source, "generated": generated})
    write_json(output / "ComparisonPreflight.json", {"cases": preflight, "passed": all(case["passed"] for case in preflight),
                                                    "native_runtime_executed": False, "comparison_observations_only": True})
    sources = {**host["source_artifacts"], "HostPreparation.json": arguments.host_preparation_sha256,
               "ComparisonPreflight.json": digest((output / "ComparisonPreflight.json").read_bytes())}
    tools = output / "Tools"
    tools.mkdir(exist_ok=False)
    for name in TOOL_NAMES:
        copyfile(method_source(name), tools / name)
    tool_hashes = {name: digest((tools / name).read_bytes()) for name in TOOL_NAMES}
    write_json(tools / "GuestTools.json", tool_hashes)
    job = {"schema": SCHEMA, "mode": host["mode"], "oracle_sha256": ORACLE_SHA256, "native_acceptance": False,
           "source_specs_sha256": host["source_specs_sha256"], "source_lock_sha256": host["source_lock_sha256"],
           "writer_discovery_profile_qualified": host["writer_discovery_profile_qualified"], "source_artifacts": sources,
           "control": control, "cases": cases, "comparison_exclusions": {
               "path_role_fields": ["reference_name", "resolved_reference_path"], "volatile_fields": ["child_update_stamp"]}}
    write_json(output / "Trial.json", job)
    packet_sha, tools_sha, runner_sha = digest((output / "Trial.json").read_bytes()), digest((tools / "GuestTools.json").read_bytes()), tool_hashes["InspectBlindDrawing.py"]
    checked = subprocess.run([sys.executable, "-B", str(tools / "InspectBlindDrawing.py"), str(output / "Trial.json"),
        "--packet-sha256", packet_sha, "--tools-sha256", tools_sha, "--runner-sha256", runner_sha, "--verify-only"],
        capture_output=True, timeout=30)
    require(checked.returncode == 0, checked.stderr.decode("utf-8", errors="replace"))
    return {"packet": str(output / "Trial.json"), "packet_sha256": packet_sha, "tools_sha256": tools_sha,
            "runner_sha256": runner_sha, "comparison_preflight_passed": all(case["passed"] for case in preflight),
            "host_verify_only": json.loads(checked.stdout)}


def main():
    parser = argparse.ArgumentParser(description="Generate blind drawing inputs before attaching native comparison-only evidence")
    commands = parser.add_subparsers(dest="operation", required=True)
    generate_parser = commands.add_parser("generate")
    for name in ("source-lock", "specs", "neutral-binding", "output", "writer-root", "writer-sources"):
        generate_parser.add_argument("--" + name, type=Path, required=True)
    for name in ("source-lock-sha256", "specs-sha256", "neutral-binding-sha256", "windows-directory", "writer-sources-sha256"):
        generate_parser.add_argument("--" + name, required=True)
    generate_parser.add_argument("--case", action="append", required=True)
    generate_parser.add_argument("--disclosed", action="store_true")
    for name in ("profile-result", "profile-sources"):
        generate_parser.add_argument("--" + name, type=Path)
        generate_parser.add_argument("--" + name + "-sha256")
    attach_parser = commands.add_parser("attach-comparison")
    attach_parser.add_argument("--output", type=Path, required=True)
    attach_parser.add_argument("--corpus", type=Path, required=True)
    attach_parser.add_argument("--host-preparation-sha256", required=True)
    arguments = parser.parse_args()
    result = generate_host(arguments) if arguments.operation == "generate" else attach_comparison(arguments)
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
