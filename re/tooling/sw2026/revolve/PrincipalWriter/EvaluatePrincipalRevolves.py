from argparse import ArgumentParser
from base64 import b64decode, b64encode
import codecs
from hashlib import sha256
from importlib import import_module
from io import BytesIO
import json
from math import cos, isclose, isfinite, radians, sin
import os
from pathlib import Path, PureWindowsPath
import re
from subprocess import check_output, run
from tarfile import TarInfo, open as open_tar
import sys
import time


HERE = Path(__file__).resolve()
HOST = Path("/Users/odin/Documents/UniCAD/Oracle121Takeover")
SHARE = PureWindowsPath(r"\\Mac\Home\Documents\UniCAD\Oracle121Takeover")
OLD = PureWindowsPath(r"C:\KitSdkCandidates\PrincipalRevolveSources01")
LOCK_PATH = "re/solidworks/v2026/heldout/PrincipalRevolveSourceLock01.json"
LOCK_SHA = "9396b94d1d503a0389c1db4ce7711125429265b271694bbe28a890b49059dc48"
SPEC_SHA = "13be8abb8186c7a876637ea27e93c0b35083c0ea34cbf4b052d3b8988a81e457"
CONTROL = "GeneratedOrdinaryRevolveNative01/Control/RevolveFull.SLDPRT"
CONTROL_SHA = "28e1f9cd045a7a264b2bdf8658ae593744d65ca708def4a48199ec357f063ab0"
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
VERSION = "34.5.2.0604"
WRITER = "b503656075e6934107884e15fd041705bf5c07f0"
SOURCE_TREE = "c1967f83c511b6ffc699684335e132704851a1fb"
FIRST = "2e9d58ae807c86f93f87f7362e4be1ca32d0aa34"
LOCK_COMMIT = "804c4f0475298ff034e374c459a7cb25e05210f5"
DISCLOSED = "re/solidworks/measurements/2026/SdkPrincipalRevolveNative01.json"
DISCLOSED_SHA = "fef0d912ecf4409ea294af34c5b70bd9e16080ab2e8dccd79af992f6811e10d8"
PROTOCOL = "re/solidworks/records/PrincipalRevolveHeldoutProtocol2026.md"
TOOLS = "re/tooling/sw2026"
REVOLVE = TOOLS + "/revolve"
EVALUATOR = REVOLVE + "/PrincipalWriter/EvaluatePrincipalRevolves.py"
BUILDER = REVOLVE + "/PrincipalWriter/BuildPrincipalRevolves.py"
COMPARER = REVOLVE + "/PrincipalWriter/ComparePrincipalRevolves.py"
PACKED = (
    LOCK_PATH, DISCLOSED, PROTOCOL, EVALUATOR, BUILDER, COMPARER,
    *(TOOLS + "/" + name for name in (
        "AuthorCurves.py", "AuthorRevolveSources.py", "InspectFresh.py", "OracleIdentity.py", "Swapp.py",
    )),
    *(REVOLVE + "/Preparation/" + name for name in (
        "MakeRevolveRequest01.py", "ReadRevolveInput01.py", "RevolveStreamAudit02.py",
    )),
    REVOLVE + "/PrincipalReader/AuditPrincipalReader.py",
    REVOLVE + "/Construction/SdkRevolveObserver01.py",
    REVOLVE + "/Construction/SdkRevolveTree01.py",
)
CASES = {"PrincipalRevolveHeldoutRight": "right", "PrincipalRevolveHeldoutTop": "top"}
CASE_FIELDS = {"name", "split", "plane", "radius_m", "axial_m", "axis_x_m", "axis_axial_m",
               "angle_deg", "reverse", "edit_angle_deg"}
SCHEMA = "kit.sw2026.principal-revolve-heldout-evaluation.v1"
FRAMES = {
    "right": ((0, 0, -1), (0, 1, 0), (1, 0, 0)),
    "top": ((1, 0, 0), (0, 0, -1), (0, 1, 0)),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(raw):
    return sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def checked(path, expected):
    require(path.is_file() and not path.is_symlink(), f"missing or redirected file {path.name}")
    raw = path.read_bytes()
    require(digest(raw) == expected, f"changed file {path.name}")
    return raw


def publish(path, raw):
    with path.open("xb") as stream:
        stream.write(raw)
    return digest(raw)


def locked_slots(lock):
    require(lock["passed"] and lock["heldout_results_sealed"] and lock["writer_output_count"] == 0
            and lock["distinct_processes"] == 12 and lock["control_before_healthy"] and lock["control_after_healthy"]
            and lock["specs_sha256"] == SPEC_SHA and lock["oracle_sha256"] == ORACLE
            and lock["control_sha256"] == CONTROL_SHA, "invalid pre-writer native lock")
    rows = {row["name"]: row for row in lock["cases"] if row["split"] == "heldout"}
    require(set(rows) == set(CASES) and all(row["passed"] and row["dimension_edit_passed"]
            and len(row["phase_record_sha256"]) == 2 for row in rows.values()), "wrong pre-writer slot inventory")
    return rows


def pack(source, research):
    output = BytesIO()
    with open_tar(fileobj=BytesIO(source), mode="r:") as sdk, open_tar(fileobj=output, mode="w:gz") as bundle:
        for entry in sdk:
            bundle.addfile(entry, sdk.extractfile(entry) if entry.isfile() else None)
        for name, payload in sorted(research.items()):
            entry = TarInfo(name)
            entry.size = len(payload)
            entry.mode = 0o644
            bundle.addfile(entry, BytesIO(payload))
    return output.getvalue()


def freeze(name):
    require(os.name != "nt" and re.fullmatch(r"PrincipalRevolveEvaluation\d{2}", name) is not None,
            "use a fresh principal revolve host packet")
    repo = HERE.parents[5]
    root = HOST / name
    require(not root.exists(), "packet already exists")

    def git(*args):
        return check_output(("git", "-C", str(repo), *args))

    method = git("rev-parse", "HEAD").decode().strip()
    for parent, child in ((LOCK_COMMIT, FIRST), (FIRST, WRITER), (WRITER, method)):
        git("merge-base", "--is-ancestor", parent, child)
    tree = git("rev-parse", f"{WRITER}:src").decode().strip()
    require(tree == SOURCE_TREE, "package does not use the disclosed writer tree")
    exact = {name: git("show", f"{method}:{name}") for name in PACKED}
    lock = json.loads(exact[LOCK_PATH])
    locked_slots(lock)
    first_written = int(git("show", "--no-patch", "--format=%ct", FIRST))
    evaluated = json.loads(exact[DISCLOSED])
    require(digest(exact[LOCK_PATH]) == LOCK_SHA and lock["finished_at"] < first_written < time.time()
            and digest(exact[DISCLOSED]) == DISCLOSED_SHA and evaluated["source_tree"] == tree
            and evaluated["controls_healthy"] and evaluated["distinct_processes"] == 10
            and len(evaluated["cases"]) == 4, "writer chronology or disclosed acceptance differs")
    require(exact[EVALUATOR] == HERE.read_bytes(), "running a different method from the committed code")
    checked(HOST / CONTROL, CONTROL_SHA)
    package = pack(git("archive", "--format=tar", WRITER, "src"), exact)
    value = {
        "schema": SCHEMA, "method_revision": method, "writer_revision": WRITER, "source_tree": tree,
        "first_orientation_writer": FIRST, "first_orientation_writer_epoch": first_written,
        "locked_at": lock["finished_at"], "write_epoch": int(time.time()), "source_lock_sha256": LOCK_SHA,
        "control_sha256": CONTROL_SHA, "disclosed_sha256": DISCLOSED_SHA, "spec_sha256": SPEC_SHA,
        "oracle_sha256": ORACLE, "oracle_version": VERSION,
        "guest_packet": str(SHARE / name), "private": str(OLD.parent / name),
        "archive_sha256": digest(package), "method_sha256": digest(exact[EVALUATOR]),
        "files": {key: digest(raw) for key, raw in sorted(exact.items())},
        "case_source_sha256": {key: row["native_sha256"] for key, row in locked_slots(lock).items()},
        "sealed_reads": 0,
    }
    root.mkdir(mode=0o700)
    publish(root / HERE.name, exact[EVALUATOR])
    publish(root / "Code.tar.gz", package)
    pin = publish(root / "Freeze.json", encode(value))
    return {"packet": str(root), "freeze_sha256": pin, "source_tree": tree, "sealed_reads": 0}


def packet(path, pin):
    require(os.name == "nt" and path.name == "Freeze.json", "run the frozen guest phases in Windows")
    manifest = json.loads(checked(path, pin))
    require(manifest["schema"] == SCHEMA and manifest["source_tree"] == SOURCE_TREE
            and manifest["writer_revision"] == WRITER and manifest["source_lock_sha256"] == LOCK_SHA
            and manifest["spec_sha256"] == SPEC_SHA and manifest["disclosed_sha256"] == DISCLOSED_SHA
            and manifest["oracle_sha256"] == ORACLE and manifest["control_sha256"] == CONTROL_SHA
            and Path(manifest["guest_packet"]) == path.parent and HERE == path.parent / HERE.name
            and digest(HERE.read_bytes()) == manifest["method_sha256"], "wrong principal revolve freeze")
    private = Path(manifest["private"])
    require(private == Path(OLD.parent) / path.parent.name and not private.is_symlink(),
            "private output root overlaps or redirects the input")
    archive = checked(path.parent / "Code.tar.gz", manifest["archive_sha256"])
    return manifest, private, archive


def code(archive, private, manifest, *, create):
    target = private / "Code"
    with open_tar(fileobj=BytesIO(archive), mode="r:gz") as bundle:
        rows = bundle.getmembers()
        allowed = set(PACKED)
        names = [row.name for row in rows]
        require(len({name.casefold() for name in names}) == len(rows)
                and all((row.isfile() or row.isdir()) and not name.startswith("/") and "\\" not in name
                        and ".." not in PureWindowsPath(name).parts and ":" not in name
                        and (name == "src" or name.startswith("src/") or name in allowed
                             or (row.isdir() and any(value.startswith(name + "/") for value in allowed)))
                        for row, name in zip(rows, names, strict=True)), "invalid frozen code inventory")
        if create:
            target.mkdir(parents=True, exist_ok=False)
            bundle.extractall(target, members=rows, filter="data")
        files = {row.name: row for row in rows if row.isfile()}
        observed = {path.relative_to(target).as_posix() for path in target.rglob("*") if path.is_file()}
        require(set(files) == observed, "extracted code inventory differs")
        for name, row in files.items():
            item = target / name
            require(not item.is_symlink() and item.read_bytes() == bundle.extractfile(row).read(),
                    f"extracted code differs: {name}")
    for name, pin in manifest["files"].items():
        checked(target / name, pin)
    return target


def invoke(tool, args, data):
    result = run((sys.executable, "-I", "-S", "-B", str(tool), *args), input=encode(data),
                 capture_output=True, check=False, timeout=110)
    if result.returncode or result.stderr:
        lines = result.stderr.decode(errors="replace").splitlines()
        raise ValueError("guarded SDK worker failed: " + (lines[-1] if lines else str(result.returncode)))
    return json.loads(result.stdout)


def predict(case, degrees):
    ri, ro = case["radius_m"]
    lo, hi = case["axial_m"]
    angle = radians(degrees)
    length = hi - lo
    delta = ro**2 - ri**2
    q = 2 * (ro**3 - ri**3) / (3 * angle * delta)
    volume = length * angle * delta / 2
    x = case["axis_x_m"] + q * sin(angle)
    y = (lo + hi) / 2
    z = (1 if case["reverse"] else -1) * q * (1 - cos(angle))
    center = tuple(x * u + y * v + z * n for u, v, n in zip(*FRAMES[case["plane"]], strict=True))
    return {"angle": angle, "mass": volume, "volume": volume,
            "area": length * angle * (ri + ro) + angle * delta + 2 * length * (ro - ri), "center": center}


def authored_case(case, name):
    require(set(case) == CASE_FIELDS and case["name"] == name and case["split"] == "heldout"
            and case["plane"] == CASES[name] and type(case["reverse"]) is bool, "unowned source intent")
    ri, ro = case["radius_m"]
    lo, hi = case["axial_m"]
    a, b = case["axis_axial_m"]
    angle, edit = case["angle_deg"], case["edit_angle_deg"]
    require(all(type(value) in (int, float) and isfinite(value)
                for value in (ri, ro, lo, hi, a, b, angle, edit, case["axis_x_m"]))
            and 0 < ri < ro and a < lo < hi < b and b - a >= 1e-8 and 0 < angle < 360
            and 0 < edit < 360 and angle != edit, "unsupported locked authored geometry")
    return case


def prepare(path, pin):
    manifest, private, archive = packet(path, pin)
    require(not private.exists(), "preparation working directory already exists")
    target = code(archive, private, manifest, create=True)
    specs = json.loads(checked(Path(OLD) / "Specs.json", SPEC_SHA))
    require(specs["schema"] == "kit.sw2026.ordinary-revolve-specs.v1", "unexpected authored specification schema")
    rows = [row for row in specs["cases"] if row["split"] == "heldout"]
    require(len(rows) == 2 and {row["name"] for row in rows} == set(CASES), "wrong two locked intent rows")
    candidates = private / "Candidate"
    candidates.mkdir()
    evidence = {}
    for row in rows:
        case = authored_case(row, row["name"])
        name = "Kit" + case["name"]
        candidate = candidates / (name + ".SLDPRT")
        spec = {"name": name, "radial_mm": [value * 1000 for value in case["radius_m"]],
                "axial_mm": [value * 1000 for value in case["axial_m"]], "axis_x_mm": case["axis_x_m"] * 1000,
                "axis_span_mm": [value * 1000 for value in case["axis_axial_m"]], "angle_deg": case["angle_deg"],
                "reverse": case["reverse"], "edit_angle_deg": case["edit_angle_deg"],
                "created_at": manifest["write_epoch"], "self_path": str(candidate)}
        request = {"plane": case["plane"], "spec": spec}
        proof = invoke(target / BUILDER, ("--worker",), request)
        raw = b64decode(proof.pop("output"), validate=True)
        require(digest(raw) == proof["sha256"] and len(raw) == proof["bytes"]
                and not proof["external_access_attempts"] and proof["caller_stream_untouched"]
                and proof["path_and_named_stream_equal"] and len(proof["archive_streams"]) == 10,
                "candidate construction did not preserve exact guarded writer outputs")
        publish(candidate, raw)
        evidence[case["name"]] = {
            "intent": case, "generated": proof, "neutral_request_sha256": digest(encode(request)),
            "initial_prediction": predict(case, case["angle_deg"]), "edited_prediction": predict(case, case["edit_angle_deg"]),
        }
    generation = {"schema": SCHEMA, "freeze_sha256": pin, "cases": evidence,
                  "original_files_read": 0, "native_processes": 0}
    generation_sha = publish(private / "Generation.json", encode(generation))
    return {"generation_sha256": generation_sha, "freeze_sha256": pin, "original_files_read": 0,
            "candidates": {name: row["generated"]["sha256"] for name, row in evidence.items()}}


def sdk_read(root, request):
    sys.path[:0] = [str(root / "src"), str(root / REVOLVE / "Preparation"), str(root / REVOLVE / "PrincipalReader")]
    from AuditPrincipalReader import check_projection, make_guard
    from RevolveStreamAudit02 import stream_audit
    from convert import open_document
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    from convert.adapters.solidworks.Core.TypedResolved.Revolves.ReadRevOwners import ReadRevOwners

    for encoding in ("ascii", "utf-8", "utf-8-sig", "utf-16-le", "utf-16-be", "latin-1"):
        codecs.lookup(encoding)
    for name in ("interchange.brep.Validation.BrepValidate", "interchange.document.Behavior.DocumentIo",
                 "interchange.document.Models.DocumentProvenance", "interchange.document.Models.DocumentWalk",
                 "interchange.document.Validation.AngleRevValidate", "interchange.document.Validation.DocumentAssemblyValidate",
                 "interchange.document.Validation.DocumentFeatureValidate", "interchange.document.Validation.DocumentReferenceValidate",
                 "interchange.document.Validation.PlaneRevValidate", "interchange.document.Validation.DistExtValidate"):
        import_module(name)
    raw = b64decode(request["input"], validate=True)
    require(digest(raw) == request["sha256"], "stdin file fingerprint differs")
    case, angle = request["intent"], request["radians"]
    plane = case["plane"]
    state, guard = make_guard(root / "src")
    state["enabled"] = True
    try:
        archive = SldprtArchive.from_bytes(raw)
        link = ReadNativeLink(archive, 0)
        (owner,) = ReadRevOwners(link)
        assert owner.AngleValue.NameValue == "D1" and owner.IsReverse == case["reverse"]
        assert isclose(owner.AngleValue.RadiansValue, angle, rel_tol=1e-12)
        streams, metadata = stream_audit(archive, link)
        assert len(streams) == 8 and len(metadata) == 2 and all(row["qualified"] for row in metadata.values())
        doc = open_document(raw, source_format="solidworks.sldprt", strict=True, include_tessellation=False)
        doc.assert_valid()
        assert doc.brep is not None and len(doc.brep.bodies) == len(doc.bodies) == 1
        assert bool(doc.brep_payloads) == request["saved"]
        (axis,) = [value for value in doc.sketches[0].entities if value.construction]
        local = tuple((p.x, p.y) for p in (axis.geometry.start, axis.geometry.end))
        for pair, expected_y in zip(local, case["axis_axial_m"], strict=True):
            assert isclose(pair[0], case["axis_x_m"] * 1000, abs_tol=1e-11)
            assert isclose(pair[1], expected_y * 1000, abs_tol=1e-11)
        ref = owner.ProfileValue.FieldsValue["pd_f78"]
        assert ref.FieldsValue["f100"] == {"right": 1, "top": 2}[plane]
        native_id = ref.FieldsValue["ff0"]["f00"]
        projection = check_projection(doc, plane, native_id, local, owner.AngleValue.RadiansValue, case["reverse"])
        assert doc.bodies[0].final_feature_id == projection["feature"]
    finally:
        state["enabled"] = False
    assert not guard["unexpected_attempts"]
    return {"input_sha256": request["sha256"], "body_name": doc.bodies[0].name, "saved_body_cache": request["saved"],
            "projection": projection, "streams": streams | metadata, "guard": guard}


def compare_prediction(snapshot, case, expected):
    assert snapshot["bodies"] == 1 and snapshot["forward_handedness"] == -1 and snapshot["reverse"] == case["reverse"]
    assert isclose(snapshot["angle_radians"], expected["angle"], rel_tol=2e-7)
    actual = snapshot["mass"]
    for key in ("mass", "volume", "area"):
        assert isclose(actual[key], expected[key], rel_tol=2e-7)
    for value, target in zip(actual["com"], expected["center"], strict=True):
        assert isclose(value, target, rel_tol=2e-7, abs_tol=1e-10)
    frame = ((0, 0, 0), *FRAMES[case["plane"]])
    for values, targets in zip(snapshot["profile"]["frame_points"], frame, strict=True):
        assert all(isclose(a, b, abs_tol=1e-12) for a, b in zip(values, targets, strict=True))


def native_phase(root, case, source, input_sha, edited, result_path):
    import AuthorRevolveSources as author
    from ComparePrincipalRevolves import compliant
    from SdkRevolveObserver01 import SdkRevolveObserver
    from SdkRevolveTree01 import predict_tree
    import Swapp

    data = checked(source, input_sha)
    already_edited = edited is None
    first_angle = case["edit_angle_deg"] if already_edited else case["angle_deg"]
    target = case | {"name": source.stem, "angle_deg": first_angle}
    sdk = invoke(root / EVALUATOR, ("read", "--root", str(root)), {
        "input": b64encode(data).decode("ascii"), "sha256": input_sha, "intent": case,
        "radians": radians(first_angle), "saved": already_edited or source.stem == case["name"],
    })
    original_controller = Swapp.Sw

    class ObserveReadOnly(original_controller):
        def open(self, path, doctype=None, *, read_only=False):
            return super().open(path, doctype, read_only=True)

    class PrincipalObserver(SdkRevolveObserver):
        expected_trees = {target["name"]: predict_tree(target)}

        def snapshot(self, current, label, angle_degrees):
            assert os.path.samefile(str(self.get(self.model, "GetPathName")), source)
            assert self.get(self.model, "IsOpenedReadOnly")
            preference = self.display_dimension_preference()
            previous = bool(self.get(self.model, "GetUserPreferenceToggle", preference))
            if not previous:
                self.get(self.model, "SetUserPreferenceToggle", preference, True)
            try:
                feature = super().snapshot(current, label, angle_degrees)
            finally:
                if not previous:
                    self.get(self.model, "SetUserPreferenceToggle", preference, False)
                assert bool(self.get(self.model, "GetUserPreferenceToggle", preference)) == previous
            record = self.rec.data[label]
            expected = predict(case, angle_degrees)
            compare_prediction(record, case, expected)
            dims = [row for node in record["features"] if node["type"] == "Revolution" for row in node.get("dims", ())]
            assert len(dims) == 1 and dims[0]["name"] == f"D1@OrdinaryBossRevolve@{source.stem}.Part"
            assert isclose(dims[0]["value"], expected["angle"], rel_tol=1e-12)
            (body,) = tuple(self.get(self.model, "GetBodies2", 0, False) or ())
            record["body_name"] = self.get(body, "Name")
            require(isinstance(record["body_name"], str) and record["body_name"], "native body label unavailable")
            if sdk["saved_body_cache"]:
                require(record["body_name"] == sdk["body_name"], "saved SDK and native body labels differ")
            self.rec.flush()
            return feature

    previous = author.RevolveAuthor
    try:
        Swapp.sweep()
        Swapp.Sw, author.RevolveAuthor = ObserveReadOnly, PrincipalObserver
        report, pin = author.run_phase(target, "edited-reopen" if already_edited else "reopen", source, ORACLE,
                                       input_sha, inspect_before_rebuild=True, inspect_profile=True,
                                       record_path=result_path, save_edited=edited)
    finally:
        Swapp.Sw, author.RevolveAuthor = original_controller, previous
    require(report["passed"], f"native phase failed at {result_path.name}")
    compliant(report)
    initial = report["before_explicit_rebuild"]
    require((initial["bodies"], initial["needs_rebuild"], initial["whats_wrong"]) == (1, 0, 0),
            f"initial native model differs in {result_path.name}")
    if not already_edited:
        assert report["edit"]["passed"] and report["edit"]["setter_status"] == 0
        assert report["display_dimension_preference"]["restored"]
        assert report["edited_derivative"]["save_status"] == [True, 0, 0]
        checked(edited, report["edited_derivative"]["sha256"])
    return report, {"native_receipt_sha256": pin, "sdk": sdk,
                    "oracle_process": report["oracle_identity"]["process_creation_filetime"]}


def source_lifecycle(root, private, row, locked, output):
    from ComparePrincipalRevolves import compare, compliant

    case = row["intent"]
    raw_name = case["name"]
    old = Path(OLD) / "Sources" / "heldout" / raw_name
    reference = old / (raw_name + ".SLDPRT")
    original_pin = locked["native_sha256"]
    assert len(checked(reference, original_pin)) == locked["native_bytes"]
    for phase, pin in zip(("author", "reopen"), locked["phase_record_sha256"], strict=True):
        checked(old / (raw_name + f".{phase}.json"), pin)
    original_capture = json.loads(checked(old / (raw_name + ".reopen.json"), locked["phase_record_sha256"][1]))
    compliant(original_capture)
    raw_generated_sha = row["generated"]["sha256"]
    generated = private / "Candidate" / ("Kit" + raw_name + ".SLDPRT")
    measured = {}
    receipts = {}
    for kind, source, input_sha in (("source", reference, original_pin), ("generated", generated, raw_generated_sha)):
        group = output / kind
        group.mkdir()
        saved = group / "Edited" / source.name
        saved.parent.mkdir()
        first, first_receipt = native_phase(root, case, source, input_sha, saved, group / "Open.json")
        later, later_receipt = native_phase(root, case, saved, first["edited_derivative"]["sha256"], None,
                                            group / "Reopen.json")
        measured[kind] = (first["reopened"], first["edited"], later["reopened"])
        receipts[kind] = {"open": first_receipt, "reopen": later_receipt,
                          "edited_sha256": first["edited_derivative"]["sha256"]}
    for state, expected in zip(measured["source"][:2], (original_capture["reopened"], original_capture["edited"]), strict=True):
        compare(state, expected)
    matches = {}
    for label, made, wanted in zip(("open", "edited", "reopen"), measured["generated"], measured["source"], strict=True):
        require(made["complete_tree"] == wanted["complete_tree"] and len(made["complete_tree"]) == 25,
                f"recursive trees differ at {label}")
        require(made["body_name"] == wanted["body_name"], f"actual native body names differ at {label}")
        require(made["sketch_relation_count"] == wanted["sketch_relation_count"] == 4
                and not made["sketch_has_display_dimensions"] and not wanted["sketch_has_display_dimensions"],
                f"sketch relations or dimensions differ at {label}")
        matches[label] = compare(made, wanted) | {"recursive_tree_rows": len(made["complete_tree"]),
                                                 "body_name": made["body_name"]}
    checked(reference, original_pin)
    checked(generated, raw_generated_sha)
    return {"passed": True, "source_sha256": original_pin, "generated_sha256": raw_generated_sha,
            "neutral_request_sha256": row["neutral_request_sha256"], "measured": matches, "phases": receipts}


def native(path, pin, generation_sha):
    manifest, private, archive = packet(path, pin)
    root = code(archive, private, manifest, create=False)
    generation = json.loads(checked(private / "Generation.json", generation_sha))
    require(generation["schema"] == SCHEMA and generation["freeze_sha256"] == pin
            and generation["original_files_read"] == generation["native_processes"] == 0
            and set(generation["cases"]) == set(CASES), "wrong two-case generation pin")
    for name, row in generation["cases"].items():
        checked(private / "Candidate" / ("Kit" + name + ".SLDPRT"), row["generated"]["sha256"])
    slots = locked_slots(json.loads(checked(root / LOCK_PATH, LOCK_SHA)))
    sys.path[:0] = [str(root / name) for name in (TOOLS, REVOLVE + "/Construction", REVOLVE + "/PrincipalWriter")]
    from InspectFresh import healthy, inspect
    import Swapp

    output = private / "Native"
    output.mkdir()
    control = Path(SHARE / PureWindowsPath(CONTROL))
    controls = {}
    measured = {}

    def control_phase(label):
        raw = {}
        try:
            checked(control, CONTROL_SHA)
            Swapp.sweep()
            inspect(control, result=raw)
            identity = raw["oracle_identity"]
            passed = (healthy(raw) and raw["sha256"] == CONTROL_SHA
                      and identity["file_version"] == VERSION and identity["sha256"] == ORACLE)
            checked(control, CONTROL_SHA)
        except Exception as error:
            raw["exception"] = repr(error)
            passed = False
        controls[label] = {
            "passed": passed, "oracle_process": raw.get("oracle_identity", {}).get("process_creation_filetime"),
            "native_receipt_sha256": publish(output / (label + ".json"), encode(raw)),
        }
        return passed

    try:
        if control_phase("ControlBefore"):
            for name, row in generation["cases"].items():
                target = output / name
                target.mkdir()
                try:
                    measured[name] = source_lifecycle(root, private, row, slots[name], target)
                except Exception as error:
                    failure = {"passed": False, "class": type(error).__name__, "reason": str(error)}
                    measured[name] = failure | {"failure_sha256": publish(target / "Failure.json", encode(failure))}
    finally:
        control_phase("ControlAfter")
    births = [row["oracle_process"] for row in controls.values()]
    for path in sorted(output.glob("*/*/*.json")):
        if path.name in ("Open.json", "Reopen.json"):
            identity = json.loads(path.read_bytes()).get("oracle_identity", {})
            births.append(identity.get("process_creation_filetime"))
    controls_healthy = len(controls) == 2 and all(row["passed"] for row in controls.values())
    distinct = len(set(births) - {None})
    passed = (controls_healthy and set(CASES) == set(measured) and all(row["passed"] for row in measured.values())
              and len(births) == distinct == 10)
    summary = {
        "schema": SCHEMA, "passed": passed, "controls_healthy": controls_healthy, "controls": controls,
        "source_tree": manifest["source_tree"], "writer_revision": manifest["writer_revision"],
        "method_revision": manifest["method_revision"], "freeze_sha256": pin, "generation_sha256": generation_sha,
        "distinct_observed_processes": distinct, "oracle_version": VERSION, "oracle_sha256": ORACLE, "cases": measured,
        "heldout_rule_credit": 2 if passed else 0, "complete_original_source_conversion": False,
    }
    summary_sha = publish(output / "Summary.json", encode(summary))
    return {"passed": passed, "controls_healthy": controls_healthy, "distinct_observed_processes": distinct,
            "summary_sha256": summary_sha, "cases": {name: row["passed"] for name, row in measured.items()}}


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("action", choices=("freeze", "prepare", "native", "read"))
    parser.add_argument("--name")
    parser.add_argument("--packet", type=Path)
    parser.add_argument("--freeze-sha256")
    parser.add_argument("--generation-sha256")
    parser.add_argument("--root", type=Path)
    args = parser.parse_args()
    if args.action == "freeze":
        result = freeze(args.name)
    elif args.action == "prepare":
        result = prepare(args.packet.resolve(), args.freeze_sha256)
    elif args.action == "native":
        result = native(args.packet.resolve(), args.freeze_sha256, args.generation_sha256)
    else:
        result = sdk_read(args.root.resolve(), json.load(sys.stdin))
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    raise SystemExit(0 if result.get("passed", True) else 3)
