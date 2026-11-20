from __future__ import annotations

import argparse
from base64 import b64decode
from datetime import datetime, timezone
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path, PureWindowsPath
import re
import shutil
import subprocess
import sys

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parents[2]
sys.path.insert(0, str(TOOLS))

from CompareSdkCircleHeldouts import close
from PrepareSdkCircleHeldoutMethod import digest, execute, save, verify_source
from SdkCircleHeldoutRules import analytic, expected_tree, neutral_request, project_spec, require


CASES = ("H03MidPlane", "H04TwoDirections")
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
METHOD_SCHEMA = "kit.sw2026.sdk-end-condition-method.v1"
FREEZE_SCHEMA = "kit.sw2026.sdk-end-condition-generated-freeze.v1"
PHASES = ("open-save", "fresh-reopen", "edited-fresh-reopen")
METADATA = {
    "specs": ("re/tooling/sw2026/EndConditionSpecs.json", "aaa4236ab265bef3ca5211b1cae9b558ad74bf2b4069e2568f51331bf74920a0"),
    "source_lock": ("re/solidworks/v2026/heldout/EndConditionSourceLock.json", "4df0938264f7761ada1f6fbc10f2335227459e6f03960ab1baa27a0395d395fe"),
    "source_receipt": ("re/solidworks/measurements/2026/EndConditionSourceLock02.json", "128134df5a77d52e84ca6e8bd2cd491b9a59ebd48c1f8458b79ca22b88e7573d"),
    "historical_freeze": ("re/solidworks/v2026/heldout/EndConditionWriterFreeze.json", "fb208a5b8dd8cf9e033ad8450fd466e9754cf6374dc88bce68ee1bcd709a2918"),
}
NATIVE_TOOLS = (
    "AuthorCurves.py", "Swapp.py", "InspectFresh.py", "OracleIdentity.py",
    "InspectCircleSketch.py", "InspectSdkCircleHeldouts.py", "CompareSdkCircleHeldouts.py",
    "SdkCircleHeldoutRules.py",
)
NATIVE_ENTRY = "ObserveSdkEndConditionHeldouts.py"
HOST_METHOD = ("CompareSdkCircleHeldouts.py", "SdkCircleHeldoutRules.py", "PrepareSdkCircleHeldoutMethod.py")
HOST_TOOLS = (
    "PrepareSdkCircleHeldoutMethod.py", "AuthorSdkCircleRequests.py",
    "SdkBlindPartChecks.py", "SdkCircleProof.py", "CheckSdkCircleRead.py",
)
SOURCE_PATHS = (
    *(f"re/tooling/sw2026/{name}" for name in (*NATIVE_TOOLS, *HOST_TOOLS)),
    "tests/__init__.py", "tests/Convert/__init__.py", "tests/Convert/Solidworks/__init__.py",
    "tests/Convert/Solidworks/Research/ConstructionGuard.py",
    "tests/Convert/Solidworks/Research/Construction/Part/MakePlainDoc.py",
)
IDENTITY_FIELDS = ("name", "split", "sha256", "manifest_sha256")


def checked_json(path, expected):
    data = path.read_bytes()
    require(sha256(data).hexdigest() == expected, f"immutable JSON identity differs: {path.name}")
    return json.loads(data)


def metadata(arguments):
    rows = {key: checked_json(getattr(arguments, key), checksum) for key, (_, checksum) in METADATA.items()}
    lock = rows["source_lock"]
    receipt = rows["source_receipt"]
    historical = rows["historical_freeze"]
    require(rows["specs"]["schema"] == "kit-sw2026-end-source-specs/1" and
            lock["specs_sha256"] == receipt["specs_sha256"] == METADATA["specs"][1] and
            receipt["lock_sha256"] == historical["source_lock_sha256"] == METADATA["source_lock"][1] and
            receipt["all_checks_passed"] and receipt["writer_implementation_started"] is False and
            receipt["heldout_native_payloads_read"] is False and lock["writer_implementation_started"] is False and
            historical["heldout_native_payloads_inspected_before_freeze"] is False,
            "the pre-writer source and specification locks do not agree")
    for release in (lock["oracle"], historical["oracle"]):
        require(release["executable_sha256"] == ORACLE and release["file_version_words"] == [34, 5, 2, 604],
                "the original source freeze uses another executable or build")
    cases = {case["name"]: case for case in lock["cases"]}
    source_receipt = {case["name"]: case for case in receipt["source_records"]}
    old_writer_cases = {case["name"]: case for case in historical["heldout_inputs"]}
    specs = {case["name"]: case for case in rows["specs"]["cases"]}
    for name in CASES:
        for field in IDENTITY_FIELDS:
            require(cases[name][field] == source_receipt[name][field] == old_writer_cases[name][field],
                    "the original case or its manifest identity differs: " + name)
        require(cases[name]["file"] == old_writer_cases[name]["file"] and
                cases[name]["split"] == specs[name]["split"] == "heldout", "the pre-writer heldout role differs")
    control = cases["ControlCircle"]
    require(control["split"] == "control" and
            all(control["name"] in receipt[when] for when in ("controls_before", "controls_after")),
            "the original matching circle bracket is absent")
    fields = (*IDENTITY_FIELDS, "file")
    return ([{field: cases[name][field] for field in fields} for name in CASES],
            [specs[name] for name in CASES], {field: control[field] for field in fields})


def git(*arguments, input_bytes=None):
    return subprocess.run(("git", "-C", str(ROOT), *arguments), input=input_bytes,
                          check=True, capture_output=True).stdout


def snapshot_source(workspace, revision):
    require(re.fullmatch(r"[0-9a-f]{40}", revision) and
            git("rev-parse", revision + "^{commit}").decode().strip() == revision,
            "select a full immutable SDK revision")
    paths = {}
    tree = git("ls-tree", "-rz", revision, "--", "src", *SOURCE_PATHS)
    for row in tree.rstrip(b"\0").split(b"\0"):
        header, name = row.split(b"\t", 1)
        mode, kind, object_id = header.split()
        relative = Path(name.decode())
        require(mode in (b"100644", b"100755") and kind == b"blob" and
                not relative.is_absolute() and ".." not in relative.parts,
                "the SDK closure must contain tracked regular files")
        paths[relative.as_posix()] = object_id
    require(set(SOURCE_PATHS) <= set(paths) and any(name.startswith("src/") for name in paths),
            "the selected revision lacks a required SDK helper")
    names = sorted(paths)
    objects = git("cat-file", "--batch", input_bytes=b"".join(paths[name] + b"\n" for name in names))
    sdk = workspace / "SDK"
    files = {}
    with BytesIO(objects) as stream:
        for name in names:
            object_id, kind, length = stream.readline().split()
            raw = stream.read(int(length))
            require((object_id, kind, len(raw), stream.read(1)) == (paths[name], b"blob", int(length), b"\n"),
                    "Git object framing differs: " + name)
            destination = sdk / "Kit" / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("xb") as sink:
                sink.write(raw)
            files[name] = sha256(raw).hexdigest()
        require(not stream.read(), "unexpected source bytes remain")
    for name in HOST_METHOD:
        require(digest(TOOLS / name) == files[f"re/tooling/sw2026/{name}"],
                "the live host helper differs from the frozen SDK revision: " + name)
    checksum = save(sdk / "FrozenSource.json", {
        "schema": "kit.sw2026.sdk-end-condition-source.v1", "base": revision,
        "tree": git("rev-parse", revision + "^{tree}").decode().strip(),
        "file_count": len(files), "files_sha256": files,
    })
    return verify_source(sdk, checksum)


def harness_hashes():
    return {name: digest(TOOLS / name) for name in (Path(__file__).name, NATIVE_ENTRY, *HOST_METHOD)}


def circle_request(path, identity, spec, label, phase, factors=(1.0, 1.0, 1.0)):
    radial, primary, secondary = factors
    return {"path": str(path), "sha256": identity, "case": label, "phase": phase,
            "axis": {"front": "z", "top": "y", "right": "x"}[spec["plane"]],
            "feature": spec["feature_name"], "mode": spec["mode"], "center_mm": list(spec["center_mm"]),
            "radius_mm": spec["radius_mm"] * radial, "depth_mm": spec["depth_mm"] * primary,
            "second_mm": None if spec["second_mm"] is None else spec["second_mm"] * secondary,
            "reverse": spec["reverse"], "end_condition": spec["end_condition"]}


def sdk_read(sdk_root, request):
    row = execute(sdk_root, "CheckSdkCircleRead.py", "worker", request)
    expected = {"D1"} if request["second_mm"] is None else {"D1", "D2"}
    require(row["file_sha256"] == request["sha256"] and row["case"] == request["case"] and
            row["phase"] == request["phase"] and row["typed_streams_exact"] == 2 and
            set(row["owned_depths"]) == expected, "SDK driver ownership or input identity differs")
    return row


def predictions(spec):
    radial, primary = spec["radial_edit_factor"], spec["depth_edit_factor"]
    stages = {"initial": analytic(spec), "radial_edit": analytic(spec, radial),
              "primary_edit": analytic(spec, radial, primary)}
    if spec["second_mm"] is not None:
        stages["secondary_edit"] = analytic(spec, radial, primary, spec["second_edit_factor"])
    return stages


def generate(sdk_root, workspace, source, epoch):
    spec = project_spec(source)
    directory = workspace / "Generated" / spec["name"]
    directory.mkdir(parents=True)
    request = neutral_request(sdk_root, spec, epoch)
    spec_hash = save(directory / "SourceSpec.json", source)
    request_hash = save(directory / "Request.json", request)
    expected_tree_rows = expected_tree(spec, request["expected_system"])
    expected = predictions(spec)
    first = execute(sdk_root, "SdkCircleProof.py", "build", request)
    repeat = execute(sdk_root, "SdkCircleProof.py", "build", request)
    require(first == repeat, "the duplicate guarded SDK builds differ")
    prepared = execute(sdk_root, "SdkCircleProof.py", "prepare", {**request, "build": first})
    require(prepared["exact_repacked_archive"] is True and
            len(prepared["streams"]) == len(first["streams"]) == 10, "the complete typed archive did not round-trip")
    for field, absolute in (("volume_m3", 1e-22), ("area_m2", 1e-18)):
        close(first["dimensions"][field], expected["initial"][field], field, absolute)
    for actual, predicted in zip(first["dimensions"]["com_m"], expected["initial"]["com_m"], strict=True):
        close(actual, predicted, "neutral centre of mass", 1e-10)
    payload = b64decode(first.pop("blob"), validate=True)
    repeat.pop("blob")
    require(sha256(payload).hexdigest() == first["sha256"] and len(payload) == first["bytes"],
            "the generated native payload differs from the guarded build report")
    candidate = directory / (spec["name"] + ".SLDPRT")
    with candidate.open("xb") as stream:
        stream.write(payload)
    verified = sdk_read(sdk_root, circle_request(candidate, first["sha256"], spec, spec["name"], "generated-before-attachment"))
    return {"name": spec["name"], "passed": True, "spec": spec, "expected_tree": expected_tree_rows,
            "expectations": expected, "candidate_file": candidate.relative_to(workspace).as_posix(),
            "candidate_sha256": first["sha256"], "candidate_bytes": first["bytes"],
            "source_spec_sha256": spec_hash, "request_sha256": request_hash, "guarded_processes": 4,
            "build_sha256": save(directory / "Build.json", first),
            "repeat_sha256": save(directory / "Repeat.json", repeat),
            "prepare_sha256": save(directory / "Prepare.json", prepared),
            "read_sha256": save(directory / "Read.json", verified)}


def freeze(arguments):
    workspace = arguments.workspace.resolve()
    require(not workspace.exists() and not workspace.is_relative_to(ROOT),
            "use a new workspace outside the checkout")
    require(0 <= arguments.created_at <= 0xffffffff, "the authored creation epoch must fit unsigned Unix seconds")
    targets, selected, control = metadata(arguments)
    workspace.mkdir(parents=True)
    sdk = snapshot_source(workspace, arguments.revision)
    harness = harness_hashes()
    method = {"schema": METHOD_SCHEMA, "frozen_utc": datetime.now(timezone.utc).isoformat(),
              "created_at": arguments.created_at, "cases": targets, "control": control, "oracle_sha256": ORACLE,
              "sdk": sdk, "harness_sha256": harness, "metadata_sha256": {name: row[1] for name, row in METADATA.items()},
              "bracket_scope": "locked diameter-circle profile; Front blind control",
              "same_mode_comparator": "each original source against its generated case",
              "evaluation_order": ["public pre-writer scalar specifications and lock metadata", "current exact SDK closure and observers",
                                   "frozen candidates and analytic edit predictions", "original attachment by lock",
                                   "paired native lifecycle", "separate post-native SDK readback"],
              "unmeasured_before_freeze": ["native payloads in this trial", "old detailed measurements"],
              "historical_boundary": "prior research writer geometry and edit evidence predates this SDK trial; tree parity remained false"}
    method_sha = save(workspace / "Method.json", method)
    results = []
    for source in selected:
        try:
            results.append(generate(workspace / "SDK/Kit", workspace, source, arguments.created_at))
        except (ValueError, KeyError, TypeError) as error:
            results.append({"name": source["name"], "passed": False, "stage": "neutral-admission",
                            "unsupported_input_or_owner": str(error), "exception_type": type(error).__name__})
    require(verify_source(workspace / "SDK", sdk["manifest_sha256"]) == sdk and harness_hashes() == harness,
            "the method or SDK closure changed during generation")
    frozen = {"schema": FREEZE_SCHEMA, "method_sha256": method_sha, "cases": results,
              "passed": all(row["passed"] for row in results), "original_native_payloads_opened": False,
              "old_detailed_measurements_opened": False, "native_acceptance": False, "public_writer_qualified": False}
    checksum = save(workspace / "GeneratedFreeze.json", frozen)
    print(json.dumps({"passed": frozen["passed"], "method_sha256": method_sha, "generated_freeze_sha256": checksum,
                      "sdk": sdk, "cases": [{"name": row["name"], "sha256": row.get("candidate_sha256"),
                                           "reason": row.get("unsupported_input_or_owner")} for row in results]}, sort_keys=True))
    return 0 if frozen["passed"] else 3


def verify_freeze(workspace, checksum):
    frozen = checked_json(workspace / "GeneratedFreeze.json", checksum)
    method = checked_json(workspace / "Method.json", frozen["method_sha256"])
    require(frozen["schema"] == FREEZE_SCHEMA and method["schema"] == METHOD_SCHEMA and
            frozen["passed"] and all(row["passed"] for row in frozen["cases"]) and
            frozen["original_native_payloads_opened"] is False and frozen["old_detailed_measurements_opened"] is False and
            tuple(row["name"] for row in frozen["cases"]) == tuple(row["name"] for row in method["cases"]) == CASES and
            method["oracle_sha256"] == ORACLE and method["harness_sha256"] == harness_hashes(),
            "the pre-attachment evaluation state differs")
    sdk = workspace / "SDK"
    require(verify_source(sdk, method["sdk"]["manifest_sha256"]) == method["sdk"], "the frozen SDK closure differs")
    for row in frozen["cases"]:
        candidate = workspace / row["candidate_file"]
        require(not candidate.is_symlink() and candidate.resolve().is_relative_to(workspace) and
                digest(candidate) == row["candidate_sha256"] and candidate.stat().st_size == row["candidate_bytes"],
                "a frozen generated candidate differs")
        expected = {"SourceSpec.json": "source_spec_sha256", "Request.json": "request_sha256",
                    "Build.json": "build_sha256", "Repeat.json": "repeat_sha256",
                    "Prepare.json": "prepare_sha256", "Read.json": "read_sha256"}
        for name, identity in expected.items():
            require(digest(candidate.parent / name) == row[identity], "a frozen generated proof differs: " + name)
    return method, frozen, sdk / "Kit"


def locked_original(root, row):
    relative = PureWindowsPath(row["file"])
    require(not relative.anchor and ".." not in relative.parts, "the source lock locator is not relative")
    native = root.joinpath(*relative.parts)
    manifest = native.with_name("Manifest.json")
    require(not native.is_symlink() and not manifest.is_symlink() and
            native.resolve(strict=True).is_relative_to(root) and manifest.resolve(strict=True).is_relative_to(root) and
            digest(native) == row["sha256"] and digest(manifest) == row["manifest_sha256"],
            "the pre-writer original or its manifest differs: " + row["name"])
    return native


def packet_case(row, source, original, generated, guest):
    spec = row["spec"]
    model = {"name": spec["name"], "configuration_name": spec["configuration_name"], "origin_name": "Origin",
             "sketch_name": spec["sketch_name"], "extrusion_name": spec["feature_name"],
             "plane_axis": {"front": "z", "top": "y", "right": "x"}[spec["plane"]],
             "profile_kind": "circle", "feature_kind": "extrusion", "end_condition": spec["end_condition"],
             "reverse_direction": spec["reverse"], "center_m": [value * 0.001 for value in spec["center_mm"]],
             "radius_m": spec["radius_mm"] * 0.001, "depth_m": spec["depth_mm"] * 0.001,
             "circle_dimension": {"mode": spec["mode"], "fix_center": True}}
    case = {"name": row["name"], "spec": spec, "expected_tree": row["expected_tree"], "request": {"document": model},
            "reference_path": guest(original), "reference_sha256": source["sha256"],
            "generated_path": guest(generated), "generated_sha256": row["candidate_sha256"],
            "edit_factor": spec["radial_edit_factor"], "depth_edit_factor": spec["depth_edit_factor"]}
    if spec["second_mm"] is not None:
        model["reverse_depth_m"] = spec["second_mm"] * 0.001
        case["reverse_depth_edit_factor"] = spec["second_edit_factor"]
    return case


def attach(arguments):
    workspace = arguments.workspace.resolve(strict=True)
    method, frozen, sdk_root = verify_freeze(workspace, arguments.freeze_sha256)
    originals = arguments.originals.resolve(strict=True)
    shared = arguments.shared_home.resolve(strict=True)
    control = arguments.control.resolve(strict=True)
    cabin = workspace / "Packet"
    require(not cabin.exists() and workspace.is_relative_to(shared) and digest(control) == method["control"]["sha256"],
            "original circle control or proposed guest packet location differs")
    require(PureWindowsPath(arguments.checkout_guest).is_absolute(), "provide the actual guest checkout path")
    locked = [locked_original(originals, source) for source in method["cases"]]
    cabin.mkdir()

    def guest(path):
        relative = path.relative_to(shared)
        return str(PureWindowsPath(r"\\Mac\Home").joinpath(*relative.parts))

    cases, reports, unsupported, files = [], [], [], {}
    for row, source, native in zip(frozen["cases"], method["cases"], locked, strict=True):
        reference = cabin / row["name"] / "Original" / native.name
        generated = cabin / row["name"] / "Generated" / Path(row["candidate_file"]).name
        for out, origin, identity in ((reference, native, source["sha256"]),
                                      (generated, workspace / row["candidate_file"], row["candidate_sha256"])):
            out.parent.mkdir(parents=True)
            shutil.copyfile(origin, out)
            require(digest(out) == identity, "the attached input changed during copy")
            files[out.relative_to(cabin).as_posix()] = identity
        try:
            reports.append(sdk_read(sdk_root, circle_request(reference, source["sha256"], row["spec"], row["name"], "original-attachment")))
        except (ValueError, KeyError, TypeError) as error:
            unsupported.append({"name": row["name"], "stage": "original-sdk-source-projection", "reason": str(error)})
            continue
        cases.append(packet_case(row, source, reference, generated, guest))
    require(all(digest(path) == row["sha256"] for path, row in zip(locked, method["cases"], strict=True)),
            "the original source changed during attachment")
    attachment = {"schema": "kit.sw2026.sdk-end-condition-attachment.v1", "generated_freeze_sha256": arguments.freeze_sha256,
                  "passed": not unsupported and len(cases) == 2,
                  "source_checks": reports, "unsupported_inputs_or_owners": unsupported}
    attachment_sha = save(workspace / "Attachment.json", attachment)
    if not attachment["passed"]:
        print(json.dumps({"passed": False, "attachment_sha256": attachment_sha, "unsupported_inputs_or_owners": unsupported}, sort_keys=True))
        return 3
    tools = cabin / "Tools"
    tools.mkdir()
    source_files = checked_json(workspace / "SDK/FrozenSource.json", method["sdk"]["manifest_sha256"])["files_sha256"]
    for name in NATIVE_TOOLS:
        shutil.copyfile(sdk_root / "re/tooling/sw2026" / name, tools / name)
        require(digest(tools / name) == source_files["re/tooling/sw2026/" + name],
                "an exact observer dependency changed during attachment: " + name)
    shutil.copyfile(TOOLS / NATIVE_ENTRY, tools / NATIVE_ENTRY)
    require(digest(tools / NATIVE_ENTRY) == method["harness_sha256"][NATIVE_ENTRY],
            "the native recorder entry differs from the pre-attachment method")
    shutil.copyfile(control, cabin / "Control.SLDPRT")
    files["Control.SLDPRT"] = method["control"]["sha256"]
    require(digest(cabin / "Control.SLDPRT") == files["Control.SLDPRT"], "the circle control changed during copy")
    job = {"schema": "kit.sw2026.sdk-circle-original-heldouts-native.v1",
           "generator_frozen_before_original_attachment": True, "cohort_fully_admitted": True,
           "generated_freeze_sha256": arguments.freeze_sha256, "method_sha256": frozen["method_sha256"],
           "source_qualification_sha256": attachment_sha,
           "writer_source_manifest_sha256": method["sdk"]["manifest_sha256"],
           "reader_source_manifest_sha256": method["sdk"]["manifest_sha256"],
           "oracle_sha256": ORACLE, "checkout_root": arguments.checkout_guest,
           "output": str(PureWindowsPath(guest(cabin)) / "Inspection"), "control": guest(cabin / "Control.SLDPRT"),
           "control_sha256": files["Control.SLDPRT"], "tools_sha256": {path.name: digest(path) for path in sorted(tools.iterdir())},
           "files_sha256": files, "cases": cases, "unsupported_inputs_or_owners": []}
    packet_sha = save(cabin / "Packet.json", job)
    require(verify_source(workspace / "SDK", method["sdk"]["manifest_sha256"]) == method["sdk"], "the SDK changed during attachment")
    print(json.dumps({"passed": True, "packet_sha256": packet_sha, "attachment_sha256": attachment_sha}, sort_keys=True))
    return 0


def saved_file(cabin, name, phase):
    basename = PureWindowsPath(phase["saved_path"]).name
    require(basename == name + "Saved.SLDPRT", "the native saved output name differs")
    return cabin / "Inspection" / name / phase["phase"] / basename


def readback(arguments):
    workspace = arguments.workspace.resolve(strict=True)
    method, frozen, sdk_root = verify_freeze(workspace, arguments.freeze_sha256)
    cabin = workspace / "Packet"
    job = checked_json(cabin / "Packet.json", arguments.packet_sha256)
    attached = checked_json(workspace / "Attachment.json", job["source_qualification_sha256"])
    result = checked_json(cabin / "Inspection/Result.json", arguments.native_sha256)
    require(job["generated_freeze_sha256"] == attached["generated_freeze_sha256"] == arguments.freeze_sha256 and
            job["method_sha256"] == frozen["method_sha256"] and attached["passed"] and
            job["writer_source_manifest_sha256"] == job["reader_source_manifest_sha256"] == method["sdk"]["manifest_sha256"] and
            job["oracle_sha256"] == ORACLE and
            result["packet_sha256"] == arguments.packet_sha256 and result["passed"] and
            result["native_acceptance"] and result["controls_healthy"] and result["inputs_immutable"] and
            result["native_processes"] == result["distinct_processes"] == 14 and
            tuple(row["name"] for row in job["cases"]) == tuple(row["name"] for row in result["cases"]) == CASES,
            "the paired native outcome, controls, case inventory or source identity differ")
    require(all(digest(cabin / relative) == identity for relative, identity in job["files_sha256"].items()),
            "a packet input changed before readback")
    require(all(digest(cabin / "Tools" / name) == identity for name, identity in job["tools_sha256"].items()),
            "a frozen observer helper changed before readback")
    reads, unsupported = [], []
    for index, (case, observed) in enumerate(zip(job["cases"], result["cases"], strict=True)):
        expected_case = frozen["cases"][index]
        require(case["generated_sha256"] == expected_case["candidate_sha256"] and
                case["reference_sha256"] == method["cases"][index]["sha256"] and
                case["spec"] == expected_case["spec"] and case["expected_tree"] == expected_case["expected_tree"],
                "the native case diverges from the generated freeze")
        expected = (case["edit_factor"], case["depth_edit_factor"], case.get("reverse_depth_edit_factor", 1.0))
        for lane, suffix, folder in (("reference", "Reference", "Original"), ("generated", "Generated", "Generated")):
            label = case["name"] + suffix
            phases = observed["lanes"][lane]
            identity = case[lane + "_sha256"]
            require(tuple(row["phase"] for row in phases) == PHASES and
                    all(row["passed"] and row["source_immutable"] and row["oracle_identity"]["sha256"] == ORACLE for row in phases) and
                    [row["source_sha256"] for row in phases] == [identity, phases[0]["saved_sha256"], phases[1]["saved_sha256"]],
                    "a native phase is incomplete or detached from its immutable predecessor")
            basename = PureWindowsPath(case[lane + "_path"]).name
            initial = cabin / case["name"] / folder / basename
            for tag, path, checksum, factors in (
                ("input", initial, identity, (1.0, 1.0, 1.0)),
                ("first-save", saved_file(cabin, label, phases[0]), phases[0]["saved_sha256"], (1.0, 1.0, 1.0)),
                ("edited-fresh-reopen-save", saved_file(cabin, label, phases[2]), phases[2]["saved_sha256"], expected),
            ):
                try:
                    reads.append(sdk_read(sdk_root, circle_request(path, checksum, case["spec"], label, tag, factors)))
                except (ValueError, KeyError, TypeError) as error:
                    unsupported.append({"case": label, "phase": tag, "reason": str(error)})
    require(verify_source(workspace / "SDK", method["sdk"]["manifest_sha256"]) == method["sdk"], "the SDK changed during readback")
    passed = not unsupported and len(reads) == len({row["pid"] for row in reads}) == 12
    checksum = save(workspace / "Readback.json", {
        "schema": "kit.sw2026.sdk-end-condition-readback.v1", "passed": passed, "packet_sha256": arguments.packet_sha256,
        "native_sha256": arguments.native_sha256, "method_sha256": frozen["method_sha256"],
        "typed_streams_exact": 2 * len(reads), "readbacks": reads, "unsupported_inputs_or_owners": unsupported,
        "public_writer_qualified": False,
    })
    print(json.dumps({"passed": passed, "readback_sha256": checksum}, sort_keys=True))
    return 0 if passed else 3


def main():
    parser = argparse.ArgumentParser(description="Prepare the independent SDK H03/H04 evaluation")
    modes = parser.add_subparsers(dest="phase", required=True)
    build = modes.add_parser("freeze")
    build.add_argument("--workspace", type=Path, required=True)
    build.add_argument("--revision", required=True)
    build.add_argument("--created-at", type=int, default=1794974400)
    for name, (path, _) in METADATA.items():
        build.add_argument("--" + name.replace("_", "-"), type=Path, default=ROOT / path)
    build.set_defaults(action=freeze)
    stage = modes.add_parser("attach")
    stage.add_argument("--workspace", type=Path, required=True)
    stage.add_argument("--freeze-sha256", required=True)
    stage.add_argument("--originals", type=Path, required=True)
    stage.add_argument("--control", type=Path, required=True)
    stage.add_argument("--shared-home", type=Path, required=True)
    stage.add_argument("--checkout-guest", required=True)
    stage.set_defaults(action=attach)
    check = modes.add_parser("readback")
    check.add_argument("--workspace", type=Path, required=True)
    check.add_argument("--freeze-sha256", required=True)
    check.add_argument("--packet-sha256", required=True)
    check.add_argument("--native-sha256", required=True)
    check.set_defaults(action=readback)
    arguments = parser.parse_args()
    return arguments.action(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
