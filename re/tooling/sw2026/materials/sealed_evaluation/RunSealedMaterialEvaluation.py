from argparse import ArgumentParser
from base64 import b64decode
from datetime import datetime
from hashlib import sha256
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
from subprocess import run
import sys
from traceback import format_exc


HERE = Path(__file__).resolve()
SOURCE = PureWindowsPath(r"C:\KitSealedMaterialSource02")
AUTHORITY = "85d42989971b6da725e697172d17d65d9f2125c395c9096fa0ad1ce5d14aabe4"
METHOD = "5215b75cf861bb864221be9bdbeb75ac5a4fc4ae1479efb15d9dd7b7d59cc501"
WORKER = "re/tooling/sw2026/materials/PrepareMaterialHeldout.py"
PACKET_HELPER = "re/tooling/sw2026/materials/FreezeMaterialHeldoutPreparation.py"
WORKER_SHA = "348fac27a3b8959e24fbd6720c45457be5075beca5c4c8376d6fe1023066bf82"
CONTROL = "c0472f9f42bf473a9073adb997180040b7767dfae93310610f77cff9509bec57"
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
SCOPE = "origin-owned-physical-material"
PENDING = ["assigned_appearance", "numeric_catalog_identity", "material_tree"]
CASE_KEYS = {"id", "kind", "configuration", "width_m", "height_m", "depth_m", "edited_depth_m",
             "first_material_key", "second_material_key"}
METHOD_TOOLS = {
    "RunSealedMaterialEvaluation.py", "CompareMaterialStates.py", "SealAssignedMaterialSources.py",
    "RunAssignedMaterialProbe.py", "RetainAssignedMaterial.py",
}
ENVELOPE = "kit.sw2026.sealed-material-evaluation-method.v1"
RECEIPT = "kit.sw2026.sealed-material-evaluation-redacted.v1"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(payload):
    return sha256(payload).hexdigest()


def encode(value, *, compact=False):
    return (json.dumps(value, sort_keys=True, indent=None if compact else 2,
                       separators=(",", ":") if compact else None, ensure_ascii=True, allow_nan=False) + "\n").encode()


def publish(path, data):
    with path.open("xb") as output:
        output.write(data)
    return digest(data)


def valid_sha(value):
    return type(value) is str and re.fullmatch("[a-f0-9]{64}", value) is not None


def stable_path(root, name):
    relative = PurePosixPath(name)
    require(not relative.is_absolute() and ".." not in relative.parts and str(relative) == name,
            "protected member locator escaped its named inventory")
    path = root.joinpath(*relative.parts)
    require(path.resolve() == path and not any(p.is_symlink() for p in (path, *path.parents) if p.is_relative_to(root)),
            "member is not a regular file in its prescribed local directory")
    return path


def checked(path, expected):
    require(valid_sha(expected) and path.is_file() and not path.is_symlink(), "pinned member is unavailable")
    raw = path.read_bytes()
    require(digest(raw) == expected, "pinned input changed bytes")
    return raw


def task_root(path):
    require(os.name == "nt", "protected source study requires the Windows oracle owner")
    from ctypes import c_uint, c_wchar_p, windll

    value = PureWindowsPath(path)
    drive_type = windll.kernel32.GetDriveTypeW
    drive_type.argtypes = (c_wchar_p,)
    drive_type.restype = c_uint
    require(value.is_absolute() and value.drive.casefold() == "c:" and len(value.parts) == 2
            and re.fullmatch("KitSealedMaterialEvaluation[0-9]{2,}", value.name)
            and drive_type("C:\\") == 3,
            "evaluation needs a new named folder on the fixed Windows C drive")
    root = Path(value)
    require(root.resolve() == root and not root.is_symlink(), "evaluation folder is a redirected path")
    return root


def verify_packet(pin):
    packet = HERE.parent.parent
    raw = checked(stable_path(packet, "EvaluationMethod.json"), pin)
    manifest = json.loads(raw)
    require(manifest["schema"] == ENVELOPE and manifest["authority_sha256"] == AUTHORITY
            and manifest["preparation_method_sha256"] == METHOD and manifest["worker_sha256"] == WORKER_SHA
            and manifest["scope"] == SCOPE and set(manifest["tools_sha256"]) == METHOD_TOOLS
            and manifest["protected_inputs_read"] == manifest["native_processes"] == 0,
            "evaluation packet scope or exact tool closure differs")
    require({p.name for p in (packet / "Tools").iterdir()} == METHOD_TOOLS, "evaluation tool inventory differs")
    for name, expected in manifest["tools_sha256"].items():
        checked(stable_path(packet, "Tools/" + name), expected)
    proof = json.loads(checked(stable_path(packet, "DisclosedHostPreflight.json"), manifest["disclosed_preflight_sha256"]))
    require(proof["passed"] is True and proof["disclosed_source_states_compared"] == 12
            and proof["synthetic_source_members_verified"] == 32 and proof["full_source_refusals"] == 2
            and proof["native_processes"] == proof["protected_inputs_read"] == 0,
            "expected the measured disclosed-only companion preflight")
    public = json.loads(checked(stable_path(packet, "SourceAuthority.json"), AUTHORITY))
    require(public["launcher_sha256"] == manifest["tools_sha256"]["SealAssignedMaterialSources.py"],
            "source custody implementation differs from the exact sealing authority")
    return manifest, public


def checked_process(row):
    value = row.get("identity") or row["oracle_identity"]
    require(value["sha256"] == ORACLE and value["file_version"] == "34.5.2.0604" and value["version_matches"] is True
            and type(value["process_id"]) is int and value["process_id"] > 0
            and type(value["process_creation_filetime"]) is int and value["process_creation_filetime"] > 0,
            "native phase does not belong to the exact fresh oracle")
    return value["process_id"], value["process_creation_filetime"]


def check_control(value):
    require(value["sha256"] == CONTROL and value["opened"] and value["rebuilt"] and value["bodies"] > 0
            and value["mass"]["volume"] > 0 and value["open_errors"] == value["open_warnings"] == value["whats_wrong"] == 0
            and not any(value.get(key) for key in ("exception", "controller_diagnostics", "dialogs"))
            and value["features"] and all(row["error"] == 0 and row["warning"] is False and not row.get("error_query_error")
                                          for row in value["features"]),
            "old source control is not a clean immutable native observation")
    return checked_process(value)


def source_chain(root, public):
    from SealAssignedMaterialSources import COPIED, PHASES, SAVES, TOOLS, summarize

    require(public["schema"] == "kit.sw2026.private-assigned-material-source-lock.v1"
            and public["passed"] is public["controls_healthy"] is True and public["native_processes"] == 10
            and public["protected_payloads_exported"] == public["writer_outputs"] == public["heldout_comparison_credit"] == 0,
            "source lock is not the external pre-writer native authority")
    checked_members = {}

    def take(name, expected):
        data = checked(stable_path(root, name), expected)
        checked_members[name] = expected
        return data

    preflight = json.loads(take("PrivatePreflight.json", public["private_intent_commitment_sha256"]))
    require(preflight["launcher_revision"] == public["launcher_revision"]
            and preflight["tool_sha256"] == public["launcher_sha256"]
            and preflight["sdk_tree_before_material_writer"] == public["pre_writer_sdk_tree"]
            and preflight["prior_disclosed_result_sha256"] == public["disclosed_native_result_sha256"]
            and datetime.fromisoformat(preflight["locked_at_utc"]) < datetime.fromisoformat(public["completed_at_utc"]),
            "private preflight does not precede the authorized terminal lifecycle")
    job_pin = preflight["job_sha256"]
    job = json.loads(take("Job.json", job_pin))
    cases = job["cases"]
    ids = tuple(row["id"] for row in cases)
    require(len(ids) == len(set(ids)) == 2 and all(re.fullmatch("Slot[a-f0-9]{32}", slot) for slot in ids)
            and tuple(row["kind"] for row in cases) == ("corner", "center")
            and all(set(row) == CASE_KEYS for row in cases) and job["cohort_role"] == "sealed_original"
            and job["oracle_sha256"] == ORACLE and job["control_sha256"] == CONTROL
            and set(job["tools_sha256"]) == TOOLS and set(job["case_intent_sha256"]) == set(ids)
            and job["writer_outputs"] == job["heldout_inputs_read_by_preparer"] == 0,
            "private Job differs from the independently authored two-case recipe")
    declared = ({"Job.json": job_pin, "Control.SLDPRT": CONTROL, "CatalogMetadata01.json": job["catalog_metadata_sha256"],
                 "WrapperShape01.json": job["wrapper_shape_sha256"]}
                | {"Tools/" + key: pin for key, pin in job["tools_sha256"].items()}
                | {"Intent/" + slot + ".json": job["case_intent_sha256"][slot] for slot in ids})
    require(len(declared) == 13 and set(declared) == COPIED | {"Job.json", *("Intent/" + slot + ".json" for slot in ids)}
            and preflight["members"] == declared, "preflight does not bind every job and authoring input")
    for name, pin in declared.items():
        if name != "Job.json":
            take(name, pin)
    require({path.name for path in stable_path(root, "Tools").iterdir()} == TOOLS,
            "private native tool directory contains undeclared imports")
    for case in cases:
        name = "Intent/" + case["id"] + ".json"
        require(json.loads(take(name, declared[name])) == case, "case intent changed between the original lock and native job")
    result = json.loads(take("Inspection/Result.json", public["primary_native_result_sha256"]))
    lock = json.loads(take("Inspection/SourceLock.json", public["private_original_source_lock_sha256"]))
    census = summarize(result, lock, job, job_pin)
    require(all(census[k] == public[k] for k in (
        "subject_locks", "control_records_sha256", "native_processes", "numeric_candidate_checks", "controls_healthy",
    )), "private native source survey differs from the published digest-only authority")
    for role, pin in census["control_records_sha256"].items():
        record = json.loads(take("Inspection/" + role + "/Record.json", pin))
        require(Path(record["path"]) == stable_path(root, "Control.SLDPRT")
                and check_control(record) == checked_process(result["phases"][role]),
                "source control process or local file identity changed")
    for case in cases:
        slot = case["id"]
        for phase in PHASES:
            seen = result["phases"][slot + "/" + phase]
            relative = "Inspection/" + slot + "/" + phase + "/"
            take(relative + "Record.json", seen["record_sha256"])
            if phase in SAVES:
                file = seen["file"]
                name = relative + SAVES[phase]
                require(Path(file["path"]) == stable_path(root, name)
                        and len(take(name, file["sha256"])) == file["bytes"],
                        "locked source file differs at its exact native phase location")
    require(len(checked_members) == 32, "source custody census is incomplete")
    return job, result, checked_members


def preparer(packet, local, *, preflight):
    code = stable_path(packet, "CodeRoot")
    helper = stable_path(packet, "CodeRoot/" + PACKET_HELPER)
    method_file = stable_path(packet, "Method.json")
    manifest = json.loads(checked(method_file, METHOD))
    members = json.loads(checked(stable_path(packet, "CodeManifest.json"), manifest["code_manifest_sha256"]))["python_sha256"]
    checked(helper, members[PACKET_HELPER])
    require(members[WORKER] == WORKER_SHA, "pinned neutral worker changed")
    action = "preflight" if preflight else "verify"
    args = [action, str(packet), "--method-sha256", METHOD]
    if preflight:
        args += ["--output", str(local / "SyntheticWindowsPreflight.json")]
    proc = run((sys.executable, "-I", "-B", str(helper), *args), cwd=code,
               capture_output=True, timeout=600, check=False)
    if proc.returncode or proc.stderr:
        publish(local / ("Preparer" + action + ".stderr"), proc.stderr)
        raise ValueError("frozen preparation method or synthetic Windows run failed")
    verdict = json.loads(proc.stdout)
    require(verdict["verified"] is True and verdict["method_sha256"] == METHOD and verdict["python_files"] == 5894
            and verdict["native_processes"] == verdict["protected_inputs_read"] == 0,
            "frozen preparer did not complete a public custody check")
    if preflight:
        checked(local / "SyntheticWindowsPreflight.json", verdict["local_synthetic_preflight_sha256"])
    return code, verdict.get("local_synthetic_preflight_sha256")


def make_request(case, materials, target, epoch):
    emitted = {**case, "first_material_key": case["second_material_key"], "second_material_key": case["first_material_key"]}
    catalog = {key: {"database_name": row["database_name"], "name": row["name"], "density_kg_m3": row["density_si_hypothesis"]}
               for key, row in materials.items()}
    return {"schema": "kit.sw2026.neutral-material-preparation.v1", "scope": SCOPE, "case": emitted,
            "catalog": catalog, "target": {"path": str(target), "saved_at": epoch}}


def worker(code, request):
    return run((sys.executable, "-I", "-B", str(stable_path(code, WORKER)), str(code)),
               cwd=code, input=encode(request, compact=True), capture_output=True, timeout=120, check=False)


def build_case(local, code, original, materials, epoch, number):
    label = "Candidate" + str(number).zfill(2)
    target = local / "Models" / (label + ".SLDPRT")
    release = local / "Generation" / label
    release.mkdir(parents=True, exist_ok=False)
    request = make_request(original, materials, target, epoch)
    request_bytes = encode(request, compact=True)
    request_sha = publish(release / "Request.json", request_bytes)
    positive = []
    for ordinal in (1, 2):
        proc = worker(code, request)
        if proc.returncode or proc.stderr:
            publish(release / ("Worker" + str(ordinal) + ".stderr"), proc.stderr)
            raise ValueError("private guarded neutral material worker failed")
        positive.append(proc.stdout)
    require(positive[0] == positive[1], "two fresh guarded builds changed result bytes")
    refusal = worker(code, {**request, "scope": "full-source"})
    require(refusal.returncode != 0 and not refusal.stdout and b"full source preservation requires" in refusal.stderr,
            "full material-source request did not fail before emitting")
    refused = publish(release / "FullSourceRefusal.stderr", refusal.stderr)
    raw = json.loads(positive[0])
    artifact = b64decode(raw.pop("artifact_base64"), validate=True)
    scope = raw["scope"]
    picked = request["catalog"][original["second_material_key"]]
    active = raw["expectations"]["initial"]
    known = raw["typed_owners"]
    shape = raw["anchor"]
    require(raw["schema"] == "kit.sw2026.neutral-material-preparation-result.v1"
            and scope == SCOPE and raw["pending_domains"] == PENDING
            and raw["request_sha256"] == request_sha and raw["logical_locator"] == str(target)
            and raw["candidate_sha256"] == digest(artifact) and raw["candidate_bytes"] == len(artifact)
            and raw["runtime_input_or_cad_access_attempts"] == 0
            and raw["native_acceptance"] is raw["full_source_preserved"] is False
            and known["part_density"] == known["config_density"] == active["density_kg_m3"] == picked["density_kg_m3"]
            and known["exact_linked_streams"] == 3 and known["config_identity"] ==
            PureWindowsPath(picked["database_name"]).stem + "|" + picked["name"]
            and shape["kind"] == original["kind"] and shape["written_owner_readback"] is True,
            "frozen material result differs from its selected second material and guarded geometry")
    proof_hash = publish(release / "Construction.json", encode(raw))
    artifact_hash = publish(target, artifact)
    return {"label": label, "slot": original["id"], "family": original["kind"],
            "artifact_sha256": artifact_hash, "bytes": len(artifact), "request_sha256": request_sha,
            "construction_sha256": proof_hash, "full_source_refusal_sha256": refused}


def reference_observations(cases, result, local):
    from CompareMaterialStates import PHASE_COMPARE, check_source_observation

    joined = {}
    for case in cases:
        build = json.loads(checked(local / "Generation" / case["label"] / "Construction.json", case["construction_sha256"]))
        expected = build["expectations"]
        source = {}
        for label, (phase, snap, model) in PHASE_COMPARE.items():
            observation = result["phases"][case["slot"] + "/" + phase]["states"][snap]
            check_source_observation(observation, expected[model], case["family"])
            source[label] = observation
        joined[case["label"]] = source
    return joined


def stage(args, root, public):
    code, guest_preflight = preparer(args.preparation.resolve(strict=True), root, preflight=True)
    source = Path(SOURCE)
    require(source.resolve(strict=True) == source and not source.is_symlink(), "source root moved from its private drive")
    job, original, custody = source_chain(source, public)
    (root / "Models").mkdir(exist_ok=False)
    cases = tuple(build_case(root, code, case, job["materials"], args.saved_at, index)
                  for index, case in enumerate(job["cases"], 1))
    generation = {"schema": "kit.sw2026.sealed-material-generation.v1", "authority_sha256": AUTHORITY,
                  "preparation_method_sha256": METHOD, "local_synthetic_preflight_sha256": guest_preflight,
                  "evaluation_method_sha256": args.evaluation_sha256, "cases": cases,
                  "guarded_workers": 6, "eligible_full_source": False}
    payload = encode(generation)
    frozen = publish(root / "GenerationFreeze.json", payload)
    require(source_chain(source, public)[2] == custody, "source custody changed during guarded generation")
    observations = reference_observations(cases, original, root)
    private = {"schema": "kit.sw2026.sealed-material-lifecycle-plan.v1", "generation_sha256": frozen,
               "evaluation_method_sha256": args.evaluation_sha256, "authority_sha256": AUTHORITY,
               "reference_observations": observations, "source_tools_sha256": job["tools_sha256"],
               "source_custody_sha256": digest(encode(custody)), "source_controls_healthy": True}
    plan = publish(root / "LifecyclePlan.json", encode(private))
    return {"passed": True, "source_controls": 2, "source_files": 6, "source_lifetimes": 10, "candidates": 2,
            "guarded_workers": 6, "full_source_refusals": 2, "native_processes": 0, "generation_sha256": frozen,
            "lifecycle_plan_sha256": plan, "native_physical_scope_passed": False}


def open_plan(args, root, public):
    plan = json.loads(checked(stable_path(root, "LifecyclePlan.json"), args.plan_sha256))
    generation = json.loads(checked(stable_path(root, "GenerationFreeze.json"), plan["generation_sha256"]))
    require(plan["schema"] == "kit.sw2026.sealed-material-lifecycle-plan.v1" and
            generation["schema"] == "kit.sw2026.sealed-material-generation.v1" and
            plan["evaluation_method_sha256"] == generation["evaluation_method_sha256"] == args.evaluation_sha256
            and plan["authority_sha256"] == generation["authority_sha256"] == AUTHORITY
            and generation["preparation_method_sha256"] == METHOD and generation["eligible_full_source"] is False
            and generation["guarded_workers"] == 6 and plan["source_controls_healthy"] is True,
            "selection and generation commitments differ before native measurement")
    job, original, custody = source_chain(Path(SOURCE), public)
    require(digest(encode(custody)) == plan["source_custody_sha256"] and job["tools_sha256"] == plan["source_tools_sha256"],
            "locked original or native tool closure changed after generation")
    cases = generation["cases"]
    require([case["slot"] for case in cases] == [case["id"] for case in job["cases"]]
            and [case["label"] for case in cases] == ["Candidate01", "Candidate02"]
            and reference_observations(cases, original, root) == plan["reference_observations"],
            "private comparison states differ from their frozen originals")
    for case in cases:
        relative = "Generation/" + case["label"] + "/"
        checked(stable_path(root, relative + "Request.json"), case["request_sha256"])
        checked(stable_path(root, relative + "FullSourceRefusal.stderr"), case["full_source_refusal_sha256"])
        candidate = stable_path(root, "Models/" + case["label"] + ".SLDPRT")
        require(len(checked(candidate, case["artifact_sha256"])) == case["bytes"],
                "candidate does not retain its complete generated artifact custody")
    return generation, plan


def measure(args, root, public):
    generation, plan = open_plan(args, root, public)
    from CompareMaterialStates import PHASE_COMPARE, check_generated_observation, observe_anchor

    sys.path.insert(0, str(Path(SOURCE) / "Tools"))
    import Swapp
    from AuthorRectangleAnchors import control
    import RetainAssignedMaterial as retain
    import RunAssignedMaterialProbe as probe

    inspected = root / "Inspection"
    inspected.mkdir(exist_ok=False)
    report = {"schema": "kit.sw2026.sealed-material-native-comparison.v1", "cases": {}}
    seed = stable_path(Path(SOURCE), "Control.SLDPRT")
    baseline_snapshot = probe.snapshot

    def observed_phase(case, entry, expected, path, pin, output, *, edit):
        sources = plan["reference_observations"][case["label"]]

        def snapshot(author, state, label):
            _, _, key = PHASE_COMPARE[label]
            fresh = baseline_snapshot(author, state, label)
            anchor = observe_anchor(author, expected[key], case["family"], Swapp)
            check_generated_observation(fresh, anchor, sources[label], expected[key], case["family"], label)
            return {**fresh, "shape": anchor, "locked_source_comparison": True}

        probe.snapshot = snapshot
        try:
            return retain.observe(output, entry, path, pin, expected["depth_edit"]["dimensions_m"]["D1@AnchorBoss"], edit=edit)
        finally:
            probe.snapshot = baseline_snapshot

    try:
        report["before"] = control(inspected, "ControlBefore", seed)
        if report["before"]["passed"]:
            for case in generation["cases"]:
                label = case["label"]
                build = json.loads(checked(root / "Generation" / label / "Construction.json", case["construction_sha256"]))
                expected = build["expectations"]
                active = expected["initial"]
                assigned = active["part_material"]
                entry = {"configuration": active["configuration"], "geometry": active["geometry"],
                         "feature_names": ["AnchorSketch", "AnchorBoss"], "drivers_m": active["dimensions_m"],
                         "density_kg_m3": active["density_kg_m3"], "material": assigned["material"], "catalog": assigned["database"]}
                output = inspected / label
                original = stable_path(root, "Models/" + label + ".SLDPRT")
                edited = observed_phase(case, entry, expected, original, case["artifact_sha256"], output / "Edit", edit=True)
                rows = {"edit": edited}
                report["cases"][label] = rows
                if edited["passed"]:
                    saved = edited["save"]
                    path = stable_path(inspected, label + "/Edit/Published/" + original.name)
                    require(Path(saved["path"]) == path and len(checked(path, saved["sha256"])) == saved["bytes"]
                            and saved["diagnostics"] == [True, 0, 0], "native save left the intended derivative")
                    rows["reopen"] = observed_phase(case, entry, expected, path, saved["sha256"], output / "Reopen", edit=False)
    finally:
        try:
            report["after"] = control(inspected, "ControlAfter", seed)
        finally:
            report_pin = publish(inspected / "Result.json", encode(report))
    observed = [(label, rows) for label, rows in report["cases"].items()]
    lifetimes = [row for _, rows in observed for row in rows.values()]
    identities = {checked_process(row) for row in (report.get("before", {}), report["after"], *lifetimes)
                  if row.get("identity") or row.get("oracle_identity")}
    controls = report.get("before", {}).get("passed") is report["after"]["passed"] is True
    states = sum(len(row["states"]) for row in lifetimes)
    passed = (controls and len(identities) == 6 and len(observed) == 2 and len(lifetimes) == 4 and states == 12
              and all(row["passed"] and all(state["locked_source_comparison"] for state in row["states"].values())
                      for row in lifetimes))
    open_plan(args, root, public)
    return {"passed": passed, "native_physical_scope_passed": passed, "controls_healthy": controls, "native_processes": len(identities),
            "generated_native_states": states, "cases": len(observed), "lifecycle_plan_sha256": args.plan_sha256,
            "native_result_sha256": report_pin, "full_source_refusals": 2,
            "signed_extrema_compared": states * 6,
            "native_numeric_checks": sum(row["numeric_checks"] for row in lifetimes)}


def main():
    ap = ArgumentParser()
    ap.add_argument("action", choices=("verify", "prepare", "measure"))
    ap.add_argument("--evaluation-sha256", required=True)
    ap.add_argument("--preparation", type=Path)
    ap.add_argument("--local", type=Path)
    ap.add_argument("--saved-at", type=int)
    ap.add_argument("--plan-sha256")
    ap.add_argument("--receipt", type=Path)
    args = ap.parse_args()
    root = None
    preserve_local_failure = False
    tag = "frozen_method"
    details = {}
    try:
        _, public = verify_packet(args.evaluation_sha256)
        sys.path.insert(0, str(HERE.parent))
        if args.action == "verify":
            details = {"passed": True, "native_processes": 0, "protected_inputs_read": 0}
        else:
            tag = "local_custody"
            root = task_root(args.local)
            require(args.receipt is not None and not args.receipt.resolve().is_relative_to(root)
                    and not args.receipt.resolve().is_relative_to(Path(SOURCE))
                    and not args.receipt.exists() and not args.receipt.is_symlink(), "reserve a new redacted receipt outside both private roots")
            if args.action == "prepare":
                require(args.preparation is not None and type(args.saved_at) is int and 0 < args.saved_at <= 0xFFFFFFFF,
                        "preparation requires the frozen Packet02 and an explicit save event")
                root.mkdir(exist_ok=False)
                preserve_local_failure = True
                tag = "guarded_preparation"
                details = stage(args, root, public)
            else:
                require(valid_sha(args.plan_sha256), "native comparison requires the exact generation handoff pin")
                require(not (root / "Inspection").exists(), "preserve prior generated native inspection")
                preserve_local_failure = True
                tag = "native_lifecycle"
                details = measure(args, root, public)
    except Exception as error:
        if preserve_local_failure and root is not None and root.is_dir() and root.resolve() == root:
            error_path = root / ("PrepareError.txt" if args.action == "prepare" else "MeasureError.txt")
            if not error_path.exists() and args.action != "verify":
                publish(error_path, format_exc().encode())
        details = {"passed": False, "failed_stage": tag, "failure_type": type(error).__name__}
    out = {"schema": RECEIPT, "action": args.action, "scope": SCOPE, "full_source_qualified": False,
           "protected_payloads_exported": 0, "evaluation_method_sha256": args.evaluation_sha256 if valid_sha(args.evaluation_sha256) else None,
           **details}
    raw = encode(out)
    if args.receipt is not None and not args.receipt.exists() and args.action != "verify" and tag not in ("frozen_method", "local_custody"):
        publish(args.receipt, raw)
    sys.stdout.buffer.write(raw)
    raise SystemExit(0 if out["passed"] else 1)


if __name__ == "__main__":
    main()
