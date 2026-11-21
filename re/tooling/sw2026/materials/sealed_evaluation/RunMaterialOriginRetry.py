from argparse import ArgumentParser
from collections import Counter
from hashlib import sha256
import importlib
import json
from pathlib import Path
from subprocess import check_output, run
import sys
from traceback import format_exc


HERE = Path(__file__).resolve()
RELATIVE = "re/tooling/sw2026/materials/sealed_evaluation/"
BASE = "1483e8726ee6ccd962a0a605fb6533dba3e00ea7"
OLD_METHOD = "3fa3d5b218e5aeddea1f6d86653a69e44b7671e5eaa5d3cc41eea036d2422c2b"
OLD_RUNNER = "0ddbdc22b0d26a91324044e19acbd656d933864b3bf401e0f40a10a73515d19e"
OLD_PLAN = "466aa7a7c7cb5256fb086c1f57917d43444dcbe17743fb5437625e3837f986e3"
OLD_RESULT = "71d0ca74a7521907f958ed89276410d5a12934bf81b72583b197a661ca4888b1"
POINT_OWNER_PROBE = "6e822733fe51dfb0aca6dfb91b5ec70500dff7c06a808fe2fc4d93c2c7411995"
ARCHIVE_CHECK = "VerifyMaterialOriginArchive.py"
SCHEMA = "kit.sw2026.sealed-material-origin-observer-retry.v1"
INSPECTION = "Inspection02"
LABELS = ("Candidate01", "Candidate02")


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(value):
    return sha256(value).hexdigest()


def encode(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + "\n").encode()


def publish(path, data):
    with path.open("xb") as writer:
        writer.write(data)
    return digest(data)


def checked(path, pin):
    require(path.is_file() and not path.is_symlink(), "pinned retry file is unavailable")
    raw = path.read_bytes()
    require(digest(raw) == pin, "pinned retry file changed")
    return raw


def original_method(path):
    path = path.resolve(strict=True)
    checked(path / "EvaluationMethod.json", OLD_METHOD)
    checked(path / "Tools" / "RunSealedMaterialEvaluation.py", OLD_RUNNER)
    sys.path.insert(0, str(path / "Tools"))
    method = importlib.import_module("RunSealedMaterialEvaluation")
    require(Path(method.__file__).resolve() == path / "Tools" / "RunSealedMaterialEvaluation.py",
            "original evaluation loaded outside its verified packet")
    manifest, public = method.verify_packet(OLD_METHOD)
    return method, public


def verify_retry(root, pin):
    method = json.loads(checked(root / "RetryMethod.json", pin))
    require(method["schema"] == SCHEMA and method["previous_method_sha256"] == OLD_METHOD
            and method["previous_plan_sha256"] == OLD_PLAN and method["previous_failure_sha256"] == OLD_RESULT
            and method["public_origin_probe_sha256"] == POINT_OWNER_PROBE
            and set(method["tools_sha256"]) == {HERE.name, ARCHIVE_CHECK}
            and HERE.parent == root / "Tools",
            "retry method does not bind the immutable earlier attempt and documented owner probe")
    require({item.name for item in (root / "Tools").iterdir()} == {HERE.name, ARCHIVE_CHECK},
            "retry tool inventory changed")
    for name, sha in method["tools_sha256"].items():
        checked(root / "Tools" / name, sha)
    preflight = json.loads(checked(root / "SyntheticOriginProof.json", method["synthetic_archive_proof_sha256"]))
    require(set(preflight["cases"]) == {"corner", "center"} and preflight["native_processes"] == preflight["protected_inputs_read"] == 0,
            "retry method lacks the public typed owner preflight")
    return method


def prove_archive(code, verifier, raw, family):
    observed = run((sys.executable, "-I", "-B", str(verifier), str(code), family), input=raw,
                   cwd=code, capture_output=True, timeout=120, check=False)
    require(observed.returncode == 0 and not observed.stderr, "guarded typed origin replay failed")
    proof = json.loads(observed.stdout)
    require(proof["typed_origin_chain"] is True and proof["family"] == family and
            proof["artifact_sha256"] == digest(raw) and proof["denied_reads"] == 0,
            "typed origin observation does not bind the complete candidate")
    return proof


def prior_failure(old, root):
    path = old.stable_path(root, "Inspection/Result.json")
    report = json.loads(checked(path, OLD_RESULT))
    require(report["schema"] == "kit.sw2026.sealed-material-native-comparison.v1"
            and list(report["cases"]) == list(LABELS) and all(report[name]["passed"] is True for name in ("before", "after")),
            "earlier failure lacks its exact healthy native controls")
    processes = [old.checked_process(report[name]) for name in ("before", "after")]
    for tag, name in (("before", "ControlBefore"), ("after", "ControlAfter")):
        old.checked(old.stable_path(root, "Inspection/" + name + "/Record.json"), report[tag]["record_sha256"])
    for label in LABELS:
        states = report["cases"][label]
        require(set(states) == {"edit"}, "earlier attempt passed the failing observer or saved a derivative")
        row = states["edit"]
        require(row["passed"] is False and row["open_errors_warnings"] == [0, 0] and row["numeric_checks"] == 10
                and row["save"] is None and not row["states"] and not row["dialogs"] and not row["controller_diagnostics"]
                and "native coincidence does not reference the actual document Origin" in row["error"],
                "earlier attempt failed outside the documented native point-domain check")
        old.checked(old.stable_path(root, "Inspection/" + label + "/Edit/Record.json"), row["record_sha256"])
        processes.append(old.checked_process(row))
    require(len(set(processes)) == 4, "earlier failure was outside four fresh exact native lifetimes")
    return report


def same(author, left, right):
    return int(author.get(author.app, "IsSame", left, right))


def local_roles(author, point, selected, origin_owner):
    typed = author.typed(point, "SketchPoint")
    owner = author.get(typed, "GetSketch")
    require(owner is not None and same(author, typed, typed) == 1 and same(author, owner, owner) == 1
            and same(author, point, selected) == same(author, owner, origin_owner) == 0
            and same(author, owner, author.sketch) == 1,
            "external and local coincidence endpoints must be concrete distinct points owned by the dependent sketch")
    require(all(abs(value) < 1e-10 for value in author.point(typed)), "native dependent point moved from the origin")
    return typed


def owner_bindings(author, family, roles):
    model = author.model
    author.get(model, "ClearSelection2", True)
    try:
        extension = author.get(model, "Extension")
        require(author.get(extension, "SelectByID2", "Point1@Origin", "EXTSKETCHPOINT",
                           0.0, 0.0, 0.0, False, 0, author.sw.nothing(), 0),
                "actual document Origin point could not be selected")
        item = author.get(author.get(model, "SelectionManager"), "GetSelectedObject6", 1, -1)
        selected = author.typed(item, "SketchPoint")
        origin_owner = author.get(selected, "GetSketch")
        require(origin_owner is not None and same(author, selected, selected) == 1
                and same(author, origin_owner, author.sketch) == 0
                and all(abs(value) < 1e-10 for value in author.point(selected)),
                "selected model Origin has no independent owning sketch")
        manager = author.get(author.sketch, "RelationManager")
        pairs, diagonals = [], []
        for row in author.get(manager, "GetRelations", 0) or ():
            if int(author.get(row, "GetRelationType")) != 9:
                continue
            kinds = list(author.get(row, "GetEntitiesType") or ())
            entries = list(author.get(row, "GetEntities") or ())
            require(len(kinds) == len(entries) == 2, "coincidence participants are missing")
            if kinds == [2, 2]:
                pairs.append(tuple(local_roles(author, point, selected, origin_owner) for point in entries))
            else:
                require(sorted(kinds) == [2, 3], "center relation has invalid participants")
                diagonals.append((entries[kinds.index(2)], entries[kinds.index(3)]))
        require(len(pairs) == 1, "expected one actual dependent point coincidence")
        pair = pairs[0]
        proxy = [point for point in pair if int(author.get(point, "Type")) == 10]
        require(len(proxy) == 1, "coincidence must have exactly one documented type ten external proxy")
        point = pair[1] if pair[0] is proxy[0] else pair[0]
        require(tuple(author.get(point, "GetID")) != tuple(author.get(proxy[0], "GetID")),
                "external proxy and local owner are not distinct dependent point identities")
        if family == "corner":
            edge = roles["edge0"]
            actual_id = tuple(author.get(point, "GetID"))
            require(int(author.get(point, "Type")) == 0 and not diagonals
                    and any(tuple(edge["point_bindings"][end]["id"]) == actual_id
                            and all(abs(value) < 1e-10 for value in edge[end]) for end in ("start", "end")),
                    "local type zero point does not select the actual lower contour corner")
        else:
            actual = [tuple(author.get(line, "GetID")) for _, line in diagonals]
            expected = [tuple(roles["diagonal" + str(index)]["id"]) for index in range(2)]
            require(Counter(actual) == Counter(expected)
                    and all(same(author, point, center) == 1 for center, _ in diagonals),
                    "the same actual local center does not own both measured construction diagonals")
    finally:
        author.get(model, "ClearSelection2", True)


def observe_retry(old, root, output, generation, plan, proofs):
    compare = importlib.import_module("CompareMaterialStates")
    sys.path.insert(0, str(Path(old.SOURCE) / "Tools"))
    import Swapp
    from AuthorRectangleAnchors import control
    import RetainAssignedMaterial as retain
    import RunAssignedMaterialProbe as probe

    original_snapshot = probe.snapshot
    original_owner_check = compare.owner_bindings
    seed = old.stable_path(Path(old.SOURCE), "Control.SLDPRT")
    report = {"schema": SCHEMA, "previous_failure_sha256": OLD_RESULT, "cases": {}}

    def observe(case, entry, expectations, path, pin, dest, *, edit):
        sources = plan["reference_observations"][case["label"]]
        proof = proofs[case["label"]]

        def snapshot(author, row, phase):
            _, _, model = compare.PHASE_COMPARE[phase]
            baseline = original_snapshot(author, row, phase)
            compare.require(proof["typed_origin_chain"] and proof["artifact_sha256"] == case["artifact_sha256"],
                            "native origin comparison lacks a matching guarded initial archive proof")
            anchor = compare.observe_anchor(author, expectations[model], case["family"], Swapp)
            compare.check_generated_observation(baseline, anchor, sources[phase], expectations[model], case["family"], phase)
            return {**baseline, "shape": anchor, "native_proxy_verified": True, "locked_source_comparison": True}

        probe.snapshot = snapshot
        compare.owner_bindings = owner_bindings
        try:
            return retain.observe(dest, entry, path, pin, expectations["depth_edit"]["dimensions_m"]["D1@AnchorBoss"], edit=edit)
        finally:
            compare.owner_bindings = original_owner_check
            probe.snapshot = original_snapshot

    try:
        report["before"] = control(output, "ControlBefore", seed)
        if report["before"]["passed"]:
            for case in generation["cases"]:
                label = case["label"]
                build = json.loads(old.checked(root / "Generation" / label / "Construction.json", case["construction_sha256"]))
                expectations = build["expectations"]
                start = expectations["initial"]
                entry = {"configuration": start["configuration"], "geometry": start["geometry"],
                         "feature_names": ["AnchorSketch", "AnchorBoss"], "drivers_m": start["dimensions_m"],
                         "density_kg_m3": start["density_kg_m3"], "material": start["part_material"]["material"],
                         "catalog": start["part_material"]["database"]}
                initial = old.stable_path(root, "Models/" + label + ".SLDPRT")
                measured = observe(case, entry, expectations, initial, case["artifact_sha256"], output / label / "Edit", edit=True)
                rows = report["cases"][label] = {"edit": measured}
                if measured["passed"]:
                    saved = measured["save"]
                    path = old.stable_path(output, label + "/Edit/Published/" + initial.name)
                    require(Path(saved["path"]) == path and len(old.checked(path, saved["sha256"])) == saved["bytes"]
                            and saved["diagnostics"] == [True, 0, 0], "native derivative did not retain custody")
                    rows["reopen"] = observe(case, entry, expectations, path, saved["sha256"], output / label / "Reopen", edit=False)
    finally:
        try:
            report["after"] = control(output, "ControlAfter", seed)
        finally:
            report_digest = publish(output / "Result.json", encode(report))
    rows = [row for case in report["cases"].values() for row in case.values()]
    processes = {old.checked_process(row) for row in (report.get("before", {}), report["after"], *rows)
                 if row.get("identity") or row.get("oracle_identity")}
    states = sum(len(row["states"]) for row in rows)
    healthy = report.get("before", {}).get("passed") is report["after"]["passed"] is True
    passed = (healthy and len(processes) == 6 and len(rows) == 4 and states == 12
              and all(row["passed"] and all(state["native_proxy_verified"] and state["locked_source_comparison"]
                                             for state in row["states"].values()) for row in rows))
    return {"passed": passed, "controls_healthy": healthy, "native_processes": len(processes),
            "native_states": states, "signed_extrema_compared": states * 6,
            "native_numeric_checks": sum(row["numeric_checks"] for row in rows), "result_sha256": report_digest}


def retry(args):
    packet = HERE.parent.parent
    verify_retry(packet, args.retry_sha256)
    old, public = original_method(args.original)
    root = old.task_root(args.local)
    receipt = args.receipt
    require(receipt.parent == Path(r"C:\Users\odin") and receipt.suffix.casefold() == ".json"
            and receipt.resolve() == receipt and not receipt.exists() and not receipt.is_symlink(),
            "reserve an unused redacted receipt directly in the authorized local user home")
    output = root / INSPECTION
    require(not output.exists(), "retain the original failure and any previous retry")
    output.mkdir(exist_ok=False)
    args.evaluation_sha256, args.plan_sha256 = OLD_METHOD, OLD_PLAN
    phase = "original_custody"
    try:
        prior_failure(old, root)
        generation, plan = old.open_plan(args, root, public)
        phase = "typed_origin_replay"
        code, _ = old.preparer(args.preparation.resolve(strict=True), output, preflight=False)
        proofs = {}
        for case in generation["cases"]:
            source = old.stable_path(root, "Models/" + case["label"] + ".SLDPRT")
            raw = old.checked(source, case["artifact_sha256"])
            proofs[case["label"]] = prove_archive(code, HERE.with_name(ARCHIVE_CHECK), raw, case["family"])
        oracle = publish(output / "OriginProof.json", encode(proofs))
        phase = "native_lifecycle"
        facts = observe_retry(old, root, output, generation, plan, proofs)
        phase = "final_custody"
        prior_failure(old, root)
        old.open_plan(args, root, public)
        facts.update(origin_archive_proof_sha256=oracle, original_artifacts_unchanged=True)
    except Exception as error:
        publish(output / "RetryError.txt", format_exc().encode())
        facts = {"passed": False, "failed_stage": phase, "failure_type": type(error).__name__}
    result = {"schema": SCHEMA, "observer_only": True, "retry_method_sha256": args.retry_sha256,
              "previous_result_sha256": OLD_RESULT, "lifecycle_plan_sha256": OLD_PLAN,
              "native_physical_scope_passed": facts["passed"], "full_source_qualified": False,
              "protected_payloads_exported": 0, **facts}
    redacted = encode(result)
    publish(receipt, redacted)
    sys.stdout.buffer.write(redacted)
    return bool(result["passed"])


def freeze(args):
    root = HERE.parents[5]
    revision = args.revision
    require(check_output(("git", "-C", str(root), "rev-parse", revision + "^")).decode().strip() == BASE
            and check_output(("git", "-C", str(root), "rev-parse", revision + ":src")) ==
            check_output(("git", "-C", str(root), "rev-parse", BASE + ":src")),
            "observer-only retry requires an unchanged SDK tree and exact method ancestry")
    old, _ = original_method(args.original)
    output = args.output.resolve()
    tools = output / "Tools"
    tools.mkdir(parents=True, exist_ok=False)
    hashes = {}
    for name in (HERE.name, ARCHIVE_CHECK):
        raw = check_output(("git", "-C", str(root), "cat-file", "blob", revision + ":" + RELATIVE + name))
        require(raw == HERE.with_name(name).read_bytes(), "frozen retry source differs from the committed tool")
        hashes[name] = publish(tools / name, raw)
    code, _ = old.preparer(args.preparation.resolve(strict=True), output, preflight=False)
    from base64 import b64decode
    from importlib.util import module_from_spec, spec_from_file_location

    spec = spec_from_file_location("PreparationSynthetic", code / old.PACKET_HELPER)
    disclosed = module_from_spec(spec)
    spec.loader.exec_module(disclosed)
    samples = {}
    for family in ("corner", "center"):
        result = disclosed.worker(code, disclosed.synthetic_request(family))
        require(result.returncode == 0 and not result.stderr, "synthetic model guard did not pass")
        raw = b64decode(json.loads(result.stdout)["artifact_base64"], validate=True)
        samples[family] = prove_archive(code, tools / ARCHIVE_CHECK, raw, family)
    proof = publish(output / "SyntheticOriginProof.json", encode({"cases": samples, "native_processes": 0, "protected_inputs_read": 0}))
    method = encode({"schema": SCHEMA, "revision": revision, "previous_method_sha256": OLD_METHOD,
                     "previous_plan_sha256": OLD_PLAN, "previous_failure_sha256": OLD_RESULT,
                     "public_origin_probe_sha256": POINT_OWNER_PROBE, "tools_sha256": hashes,
                     "synthetic_archive_proof_sha256": proof})
    pin = publish(output / "RetryMethod.json", method)
    print(json.dumps({"retry_method_sha256": pin, "synthetic_archive_proof_sha256": proof, "tools_sha256": hashes}, sort_keys=True))


if __name__ == "__main__":
    cli = ArgumentParser()
    actions = cli.add_subparsers(dest="action", required=True)
    stage = actions.add_parser("freeze")
    stage.add_argument("--revision", required=True)
    stage.add_argument("--output", required=True, type=Path)
    job = actions.add_parser("run")
    job.add_argument("--retry-sha256", required=True)
    job.add_argument("--local", required=True, type=Path)
    job.add_argument("--receipt", required=True, type=Path)
    for command in (stage, job):
        command.add_argument("--original", required=True, type=Path)
        command.add_argument("--preparation", required=True, type=Path)
    args = cli.parse_args()
    if args.action == "freeze":
        freeze(args)
    else:
        raise SystemExit(0 if retry(args) else 1)
