from __future__ import annotations

import argparse
from base64 import b64decode
from hashlib import sha256
import json
from pathlib import Path, PureWindowsPath
import shutil
import time

from PrepareSdkCircleHeldoutMethod import digest, encoded, execute, save, verify_source
from SdkCircleHeldoutRules import analytic, expected_tree, neutral_request, project_spec, require


def verify_method(root, directory, method_sha, qualification_sha):
    method_path, qualification_path = directory / "Method.json", directory / "Qualification.json"
    require(digest(method_path) == method_sha and digest(qualification_path) == qualification_sha,
            "the pre-unseal method or source qualification differs")
    method, qualification = json.loads(method_path.read_bytes()), json.loads(qualification_path.read_bytes())
    require(qualification["passed"] and qualification["method_sha256"] == method_sha and
            not any(qualification[name] for name in ("original_specs_opened", "original_native_payloads_opened", "old_native_measurements_opened")),
            "source qualification did not precede independent input access")
    for relative, identity in method["tools"].items():
        require(digest(root / relative) == identity, "frozen evaluation source differs: " + relative)
    for name, identity in method["source_freezes"].items():
        require(digest(root / "re/solidworks/v2026/heldout" / name) == identity, "pre-writer source lock differs")
    return method


def build(root, writer, method, specs_path, output):
    require(digest(specs_path) == method["specs_sha256"], "original independent scalar specification differs")
    source = json.loads(specs_path.read_bytes())
    require(source["schema"] == "kit-sw2026-curve-source-specs/1", "expected original curve source specification")
    targets = {row["name"]: row for row in method["targets"]}
    selected = [row for row in source["cases"] if row["name"] in targets]
    require(len(selected) == len(targets) == 2 and all(row["split"] == "heldout" for row in selected),
            "only the two predeclared original circle cases may be selected")
    output.mkdir(parents=True, exist_ok=False)
    rows = []
    for case in selected:
        directory = output / case["name"]
        directory.mkdir()
        row = {"name": case["name"], "passed": False, "original_native_payload_opened": False,
               "source_spec_sha256": save(directory / "SourceSpec.json", case)}
        rows.append(row)
        try:
            spec = project_spec(case)
            request = neutral_request(writer / "Kit", spec, int(method["frozen_at_utc_epoch"]))
            row["request_sha256"] = save(directory / "Request.json", request)
            first = execute(writer / "Kit", "SdkCircleProof.py", "build", request)
            repeated = execute(writer / "Kit", "SdkCircleProof.py", "build", request)
            require(first == repeated, "frozen SDK produces different repeated bytes")
            prepared = execute(writer / "Kit", "SdkCircleProof.py", "prepare", {**request, "build": first})
            payload = b64decode(first.pop("blob"), validate=True)
            repeated.pop("blob")
            require(sha256(payload).hexdigest() == first["sha256"] and len(payload) == first["bytes"], "generated file custody differs")
            require(prepared["exact_repacked_archive"] is True and len(prepared["streams"]) == 10, "generated archive is incomplete")
            expected = analytic(spec)
            for name in ("volume_m3", "area_m2"):
                require(abs(first["dimensions"][name] - expected[name]) < 1e-15, "independent expected geometry differs")
            candidate = directory / (case["name"] + ".SLDPRT")
            with candidate.open("xb") as stream:
                stream.write(payload)
            row.update(spec=spec, expectation=expected, expected_tree=expected_tree(spec, request["expected_system"]),
                       candidate_file=str(candidate.relative_to(output)), candidate_sha256=first["sha256"],
                       stored_self_path=first["stored_self_path"], complete_streams=len(first["streams"]),
                       build_sha256=save(directory / "Build.json", first), repeat_sha256=save(directory / "Repeat.json", repeated),
                       prepare_sha256=save(directory / "Prepare.json", prepared), passed=True)
        except (ValueError, TypeError, KeyError) as error:
            row.update(unsupported_owner_or_input=str(error), exception_class=type(error).__name__)
    return rows


def attach(root, reader, method, output, generated, originals, control, shared_home, checkout_guest):
    source_lock = json.loads((root / "re/solidworks/v2026/heldout/CurveSourceLock.json").read_bytes())
    control_row = next(row for row in source_lock["cases"] if row["name"] == "ControlCircle")
    require(digest(control) == control_row["sha256"], "the pristine matching native control differs")
    tools_directory = output / "Tools"
    tools_directory.mkdir()
    old_tools = ("AuthorCurves.py", "Swapp.py", "InspectFresh.py", "OracleIdentity.py", "InspectCircleSketch.py")
    tools = {}
    reader_manifest = json.loads((reader / "FrozenSource.json").read_bytes())["files_sha256"]
    for name in old_tools:
        source = reader / "Kit/re/tooling/sw2026" / name
        require(digest(source) == reader_manifest["re/tooling/sw2026/" + name], "original qualified oracle helper differs")
        shutil.copyfile(source, tools_directory / name)
        tools[name] = digest(source)
    for name in ("InspectSdkCircleHeldouts.py", "SdkCircleHeldoutRules.py", "CompareSdkCircleHeldouts.py"):
        source = root / "re/tooling/sw2026" / name
        require(digest(source) == method["tools"]["re/tooling/sw2026/" + name], "new frozen oracle helper differs")
        shutil.copyfile(source, tools_directory / name)
        tools[name] = digest(source)
    shutil.copyfile(control, output / "Control.SLDPRT")
    targets = {row["name"]: row for row in method["targets"]}

    def guest(path):
        relative = path.resolve(strict=True).relative_to(shared_home.resolve(strict=True))
        return str(PureWindowsPath(r"\\Mac\Home").joinpath(*relative.parts))

    cases = []
    unsupported = [{"name": row["name"], "reason": row.get("unsupported_owner_or_input"), "stage": "neutral-admission"}
                   for row in generated["cases"] if not row["passed"]]
    for row in generated["cases"]:
        if not row["passed"]:
            continue
        target = targets[row["name"]]
        source = originals / target["file"]
        require(digest(source) == target["sha256"], "original held-out native payload differs")
        manifest = source.parent / "Manifest.json"
        require(digest(manifest) == target["manifest_sha256"], "original source manifest differs")
        directory = output / row["name"]
        original_directory = directory / "Original"
        original_directory.mkdir()
        original_copy = original_directory / source.name
        shutil.copyfile(source, original_copy)
        spec = row["spec"]
        read_request = {"path": str(original_copy), "sha256": target["sha256"], "case": row["name"], "phase": "original-source-qualification",
                        "axis": {"front": "z", "right": "x", "top": "y"}[spec["plane"]], "feature": spec["feature_name"],
                        "mode": spec["mode"], "center_mm": list(spec["center_mm"]), "radius_mm": spec["radius_mm"],
                        "depth_mm": spec["depth_mm"], "second_mm": spec["second_mm"], "reverse": spec["reverse"],
                        "end_condition": spec["end_condition"]}
        try:
            read_report = execute(reader / "Kit", "CheckSdkCircleRead.py", "worker", read_request)
            require(digest(original_copy) == target["sha256"], "SDK source projection modified the input")
            save(directory / "OriginalRead.json", read_report)
        except (ValueError, TypeError, KeyError) as error:
            report = {"name": row["name"], "passed": False, "stage": "original-sdk-source-projection", "reason": str(error)}
            save(directory / "OriginalRead.json", report)
            unsupported.append(report)
            continue
        model = {"name": spec["name"], "configuration_name": spec["configuration_name"], "sketch_name": spec["sketch_name"],
                 "extrusion_name": spec["feature_name"], "origin_name": "Origin", "plane_axis": {"front": "z", "top": "y", "right": "x"}[spec["plane"]],
                 "profile_kind": "circle", "feature_kind": "extrusion", "center_m": [value * 0.001 for value in spec["center_mm"]],
                 "radius_m": spec["radius_mm"] * 0.001, "depth_m": spec["depth_mm"] * 0.001,
                 "circle_dimension": {"mode": spec["mode"], "fix_center": True},
                 "end_condition": spec["end_condition"], "reverse_direction": spec["reverse"]}
        if spec["second_mm"] is not None:
            model["reverse_depth_m"] = spec["second_mm"] * 0.001
        case = {"name": row["name"], "spec": spec, "expected_tree": row["expected_tree"], "request": {"document": model},
                "reference_path": guest(original_copy), "reference_sha256": target["sha256"],
                "generated_path": guest(output / row["candidate_file"]), "generated_sha256": row["candidate_sha256"],
                "edit_factor": spec["radial_edit_factor"], "depth_edit_factor": spec["depth_edit_factor"]}
        if spec["second_mm"] is not None:
            case["reverse_depth_edit_factor"] = spec["second_edit_factor"]
        cases.append(case)
    attachment = {"schema": "kit.sw2026.sdk-circle-original-attachment.v1", "passed": not unsupported and len(cases) == 2,
                  "generated_freeze_sha256": digest(output / "GeneratedFreeze.json"), "admitted_cases": [case["name"] for case in cases],
                  "unsupported_inputs_or_owners": unsupported, "old_native_measurements_opened": False}
    save(output / "Attachment.json", attachment)
    if not cases:
        return None
    files = {str(path.relative_to(output)): digest(path) for path in sorted(output.rglob("*")) if path.is_file() and "Tools" not in path.relative_to(output).parts}
    job = {"schema": "kit.sw2026.sdk-circle-original-heldouts-native.v1", "generator_frozen_before_original_attachment": True,
           "method_sha256": generated["method_sha256"], "source_qualification_sha256": generated["qualification_sha256"],
           "writer_source_manifest_sha256": method["writer"]["manifest_sha256"], "reader_source_manifest_sha256": method["reader"]["manifest_sha256"],
           "generated_freeze_sha256": digest(output / "GeneratedFreeze.json"), "oracle_sha256": source_lock["oracle"]["executable_sha256"],
           "checkout_root": checkout_guest, "output": guest(output) + r"\Inspection", "control": guest(output / "Control.SLDPRT"),
           "control_sha256": control_row["sha256"], "tools_sha256": tools, "files_sha256": files, "cases": cases,
           "cohort_fully_admitted": attachment["passed"], "unsupported_inputs_or_owners": unsupported}
    return save(output / "Packet.json", job)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--method", type=Path, required=True)
    parser.add_argument("--method-sha256", required=True)
    parser.add_argument("--qualification-sha256", required=True)
    parser.add_argument("--writer", type=Path, required=True)
    parser.add_argument("--reader", type=Path, required=True)
    parser.add_argument("--specs", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--originals", type=Path)
    parser.add_argument("--control", type=Path)
    parser.add_argument("--shared-home", type=Path)
    parser.add_argument("--checkout-guest")
    arguments = parser.parse_args()
    root, writer, reader = arguments.root.resolve(), arguments.writer.resolve(), arguments.reader.resolve()
    method = verify_method(root, arguments.method.resolve(), arguments.method_sha256, arguments.qualification_sha256)
    verify_source(writer, method["writer"]["manifest_sha256"])
    verify_source(reader, method["reader"]["manifest_sha256"])
    output = arguments.output.resolve()
    require(not output.exists() and not output.is_relative_to(root), "choose unused private generated output")
    rows = build(root, writer, method, arguments.specs.resolve(), output)
    generated = {"schema": "kit.sw2026.sdk-circle-heldout-generated-freeze.v1", "frozen_at_utc_epoch": time.time(),
                 "method_sha256": arguments.method_sha256, "qualification_sha256": arguments.qualification_sha256,
                 "specs_sha256": method["specs_sha256"], "cases": rows, "passed": all(row["passed"] for row in rows),
                 "original_native_payloads_opened": False, "old_native_measurements_opened": False,
                 "native_acceptance": False, "public_writer_qualified": False}
    generated_sha = save(output / "GeneratedFreeze.json", generated)
    packet_sha = None
    if arguments.originals is not None:
        require(arguments.control is not None and arguments.shared_home is not None and arguments.checkout_guest,
                "original attachment requires explicit control, shared home and guest checkout paths")
        packet_sha = attach(root, reader, method, output, generated, arguments.originals.resolve(), arguments.control.resolve(),
                            arguments.shared_home.resolve(), arguments.checkout_guest)
    verify_source(writer, method["writer"]["manifest_sha256"])
    verify_source(reader, method["reader"]["manifest_sha256"])
    attachment_passed = (True if arguments.originals is None else
                         json.loads((output / "Attachment.json").read_bytes())["passed"])
    passed = generated["passed"] and attachment_passed
    print(json.dumps({"passed": passed, "generated_qualified": generated["passed"], "original_projection_qualified": attachment_passed,
                      "generated_freeze_sha256": generated_sha, "packet_sha256": packet_sha}, sort_keys=True))
    return 0 if passed else 3


if __name__ == "__main__":
    raise SystemExit(main())
