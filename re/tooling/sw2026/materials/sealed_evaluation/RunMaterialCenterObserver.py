from argparse import ArgumentParser
from collections import Counter
from functools import partial
from hashlib import sha256
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import sys
from traceback import format_exc


METHOD_PIN = "9eea9ec3e38fcb2c4c819233037f021d750b350638f042c781f842d2ac9ca871"
PREVIOUS_PIN = "1c42b3169134bb68fcf97a8b29985aa4c3d0f51dd0a557297e443ab59e397489"
RECEIPT_PIN = "0b83f85b29bbda7c83f31307ab58958ab1d903e617a964d912473f74d8074601"
SCHEMA = "kit.sw2026.sealed-material-center-observer.v1"


def require(check, message):
    if not check:
        raise ValueError(message)


def checked(path, expected):
    require(path.is_file() and not path.is_symlink(), "exact controlled input is absent")
    raw = path.read_bytes()
    require(sha256(raw).hexdigest() == expected, "exact controlled input changed")
    return raw


def load_retry(packet):
    packet = packet.resolve(strict=True)
    manifest = json.loads(checked(packet / "RetryMethod.json", METHOD_PIN))
    tool = packet / "Tools" / "RunMaterialOriginRetry.py"
    checked(tool, manifest["tools_sha256"][tool.name])
    spec = spec_from_file_location("FrozenMaterialOriginRetry", tool)
    require(spec is not None and spec.loader is not None, "frozen material observer is not importable")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    module.verify_retry(packet, METHOD_PIN)
    return module


def check_prior(root, old, origin):
    receipt = json.loads(checked(Path(r"C:\Users\odin\RedactedMaterialOriginRetry01.json"), RECEIPT_PIN))
    require(receipt["retry_method_sha256"] == METHOD_PIN and receipt["result_sha256"] == PREVIOUS_PIN
            and receipt["original_artifacts_unchanged"] is True and receipt["passed"] is False
            and receipt["controls_healthy"] is True and receipt["native_states"] == 6,
            "previous observer receipt lacks its immutable partial native result")
    directory = old.stable_path(root, "Inspection02")
    report = json.loads(checked(directory / "Result.json", PREVIOUS_PIN))
    require(report["schema"] == origin.SCHEMA and report["previous_failure_sha256"] == origin.OLD_RESULT
            and list(report["cases"]) == list(origin.LABELS), "previous observer report has the wrong plan")
    processes = set()
    for label, tag in (("before", "ControlBefore"), ("after", "ControlAfter")):
        row = report[label]
        require(row["passed"], "previous observer control failed")
        checked(directory / tag / "Record.json", row["record_sha256"])
        processes.add(old.checked_process(row))
    corner, center = (report["cases"][name] for name in origin.LABELS)
    require(set(corner) == {"edit", "reopen"} and all(row["passed"] for row in corner.values())
            and len(corner["edit"]["states"]) == 4 and len(corner["reopen"]["states"]) == 2
            and set(center) == {"edit"} and center["edit"]["passed"] is False
            and "the same actual local center does not own both measured construction diagonals" in center["edit"]["error"]
            and center["edit"]["open_errors_warnings"] == [0, 0]
            and center["edit"]["save"] is None and not center["edit"]["states"],
            "previous observer failed outside the centered ownership check")
    for name in origin.LABELS:
        for phase, row in report["cases"][name].items():
            checked(directory / name / phase.capitalize() / "Record.json", row["record_sha256"])
            processes.add(old.checked_process(row))
    require(len(processes) == 5, "previous observer does not bind five distinct lifetimes")


def local_id(author, point):
    values = tuple(author.get(point, "GetID"))
    require(len(values) == 2 and all(type(value) is int for value in values),
            "native sketch entity does not have its documented local id pair")
    return values


def observe_center(origin, corner, author, family, roles):
    if family == "corner":
        return corner(author, family, roles)
    require(family == "center", "unexpected sketch family for the material observer")
    model = author.model
    author.get(model, "ClearSelection2", True)
    try:
        extension = author.get(model, "Extension")
        require(author.get(extension, "SelectByID2", "Point1@Origin", "EXTSKETCHPOINT",
                           0.0, 0.0, 0.0, False, 0, author.sw.nothing(), 0),
                "document origin could not be selected")
        found = author.get(author.get(model, "SelectionManager"), "GetSelectedObject6", 1, -1)
        selected = author.typed(found, "SketchPoint")
        origin_owner = author.get(selected, "GetSketch")
        require(origin_owner is not None and origin.same(author, selected, selected) == 1
                and origin.same(author, origin_owner, author.sketch) == 0
                and all(abs(value) < 1e-10 for value in author.point(selected)),
                "selected model origin lacks its distinct owning sketch")
        pairs, diagonals = [], []
        manager = author.get(author.sketch, "RelationManager")
        for row in author.get(manager, "GetRelations", 0) or ():
            if int(author.get(row, "GetRelationType")) != 9:
                continue
            kinds = list(author.get(row, "GetEntitiesType") or ())
            entries = list(author.get(row, "GetEntities") or ())
            require(len(kinds) == len(entries) == 2 and not author.get(row, "Suppressed"),
                    "centered coincidence must have two active participants")
            if kinds == [2, 2]:
                pairs.append(tuple(origin.local_roles(author, point, selected, origin_owner) for point in entries))
            else:
                require(sorted(kinds) == [2, 3], "centered relation does not select a point and a line")
                center = origin.local_roles(author, entries[kinds.index(2)], selected, origin_owner)
                segment = author.typed(entries[kinds.index(3)], "SketchSegment")
                owner = author.get(segment, "GetSketch")
                require(owner is not None and origin.same(author, owner, author.sketch) == 1
                        and int(author.get(segment, "GetType")) == 0
                        and bool(author.get(segment, "ConstructionGeometry")),
                        "diagonal relation does not select an actual construction line in its own sketch")
                diagonals.append((center, local_id(author, segment)))
        require(len(pairs) == 1 and len(diagonals) == 2, "centered sketch must have one proxy and two line coincidences")
        pair, = pairs
        points = {int(author.get(point, "Type")): point for point in pair}
        require(len(points) == 2 and 10 in points, "centered sketch must have one distinct external proxy")
        proxy = points.pop(10)
        point_type, point = next(iter(points.items()))
        center_key = (point_type, local_id(author, point))
        require(center_key[1] != local_id(author, proxy), "local center and external proxy reuse an identity")
        keys = [(int(author.get(center, "Type")), local_id(author, center)) for center, _ in diagonals]
        expected = [tuple(roles["diagonal" + str(index)]["id"]) for index in range(2)]
        actual = [identity for _, identity in diagonals]
        equality = tuple(origin.same(author, point, center) for center, _ in diagonals)
        author.rec.data.setdefault("center_owner_checks", []).append({
            "matches_typed_local_center": [key == center_key for key in keys],
            "matches_geometric_diagonals": Counter(actual) == Counter(expected),
            "dispatch_equality": equality,
        })
        author.rec.flush()
        require(len(set(expected)) == 2 and Counter(actual) == Counter(expected),
                "centered coincidences do not use both distinct geometric construction diagonals")
        require(all(key == center_key for key in keys),
                "both centered coincidences must bind the same typed point in the same owning sketch")
    finally:
        author.get(model, "ClearSelection2", True)


def run(args):
    origin = load_retry(args.origin_method)
    old, public = origin.original_method(args.original)
    root = old.task_root(args.local)
    target = args.receipt
    require(target.parent == Path(r"C:\Users\odin") and target.suffix.casefold() == ".json"
            and target.resolve() == target and not target.exists(), "the redacted receipt must use a new user-local path")
    args.evaluation_sha256, args.plan_sha256 = origin.OLD_METHOD, origin.OLD_PLAN
    origin.prior_failure(old, root)
    check_prior(root, old, origin)
    generation, plan = old.open_plan(args, root, public)
    output = root / "Inspection03"
    output.mkdir(exist_ok=False)
    stage = "archive_verification"
    try:
        code, _ = old.preparer(args.preparation.resolve(strict=True), output, preflight=False)
        proofs = {}
        for case in generation["cases"]:
            name = case["label"]
            candidate = old.stable_path(root, "Models/" + name + ".SLDPRT")
            raw = old.checked(candidate, case["artifact_sha256"])
            proofs[name] = origin.prove_archive(code, origin.HERE.with_name(origin.ARCHIVE_CHECK), raw, case["family"])
        archive_pin = origin.publish(output / "OriginProof.json", origin.encode(proofs))
        stage = "native_lifecycle"
        corner = origin.owner_bindings
        origin.owner_bindings = partial(observe_center, origin, corner)
        try:
            measured = origin.observe_retry(old, root, output, generation, plan, proofs)
        finally:
            origin.owner_bindings = corner
        stage = "original_custody"
        origin.prior_failure(old, root)
        check_prior(root, old, origin)
        old.open_plan(args, root, public)
        measured.update(original_artifacts_unchanged=True, origin_archive_proof_sha256=archive_pin)
    except Exception as error:
        origin.publish(output / "ObserverError.txt", format_exc().encode("utf-8"))
        measured = {"passed": False, "failed_stage": stage, "failure_type": type(error).__name__}
    report = {"schema": SCHEMA, "previous_observer_result_sha256": PREVIOUS_PIN,
              "lifecycle_plan_sha256": origin.OLD_PLAN, "protected_payloads_exported": 0,
              "full_source_qualified": False, "native_physical_scope_passed": measured["passed"], **measured}
    published = origin.encode(report)
    origin.publish(target, published)
    sys.stdout.buffer.write(published)
    return measured["passed"]


if __name__ == "__main__":
    parser = ArgumentParser()
    for parameter in ("origin-method", "original", "preparation", "local", "receipt"):
        parser.add_argument("--" + parameter, type=Path, required=True)
    raise SystemExit(0 if run(parser.parse_args()) else 1)
