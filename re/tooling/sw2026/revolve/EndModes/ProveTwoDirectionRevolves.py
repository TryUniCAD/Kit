from argparse import ArgumentParser
import codecs
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from io import BytesIO
import json
from math import isclose, radians, tau
import os
from pathlib import Path, PurePosixPath
from subprocess import check_output, run
import sys
from tarfile import TarInfo, open as open_tar


HERE = Path(__file__).resolve()
ROOT = HERE.parents[5] if len(HERE.parents) > 5 else None
BASE = "d33d2839cae07d7796d8530ec3f5a261d8c0be40"
WRITER = "59cc0c0380132f8bd03ce8b0de815b5d6b3da6e4"
TREE = "1082f9bb9b69d0b2f2ba10c0902e7694cbe9a860"
OLD_FREEZE = "ea618413f5f71fdaadd1da34b86b3aecdbf2cc27892db536bf15c1cb29983111"
GENERATION = "f36a2c4741fb9e4ddb081a40a2490c3b69f5cf968ef2da2a022b855853016216"
MIXED = "67c41678df39397433ff94cc8183f74626df40829cad61bfbeea713addd1df88"
LOCK = "977cfab507c7c77910b752bb8c46e4968a0ddfdf7efc9a8d582d99a2c7b364b9"
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
BUILD = "34.5.2.0604"
CASES = ("H-Two-01", "H-Two-02")
FORMAT = "solidworks.sldprt"
SCHEMA = "kit.sw2026.two-direction-revolve-parity.v1"
TOOLS = "re/tooling/sw2026/"
RV = TOOLS + "revolve/"
OWN = RV + "EndModes/ProveTwoDirectionRevolves.py"
BUILDER = RV + "EndModes/BuildOrdinaryEndRevolves.py"
GATE = "src/convert/adapters/solidworks/Core/Preparation/Revolve/PlanPublicRevolve.py"
MEASURED = "re/solidworks/measurements/2026/SdkOrdinaryRevolveEndHeldout01.json"
SOURCE_LOCK = "re/solidworks/measurements/2026/RevolveEndHeldoutSourceLock01.json"
FILES = (
    OWN, BUILDER, RV + "EndModes/TwoDirectionReader.py", RV + "EndModes/AuditRevEndOwners.py",
    RV + "PrincipalReader/AuditPrincipalReader.py", RV + "PrincipalWriter/BuildPrincipalRevolves.py",
    RV + "Preparation/MakeRevolveRequest01.py", RV + "Preparation/ReadRevolveInput01.py",
    RV + "Preparation/RevolveStreamAudit02.py", TOOLS + "VerifySdkCircleEndRegistration.py",
    MEASURED, SOURCE_LOCK,
)
REFUSALS = ("mid-plane", "equal-halves", "over-turn", "front", "equal-length", "translated-support", "foreign-suffix", "without-final")
MODES = ("staged", "public")


class ParityFailure(ValueError):
    pass


def need(value, check):
    if not value:
        raise ParityFailure(check)


def digest(raw):
    return sha256(raw).hexdigest()


def locked(path, sha):
    raw = path.read_bytes()
    need(digest(raw) == sha, "sealed artifact digest")
    return raw


def data(path, sha):
    return json.loads(locked(path, sha))


def json_bytes(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def publish(path, value):
    raw = json_bytes(value)
    with path.open("xb") as stream:
        stream.write(raw)
    return digest(raw)


def freeze(folder, mode):
    def git(*args):
        return check_output(("git", "-C", str(ROOT), *args))

    commit = git("rev-parse", "HEAD").decode().strip()
    delta = git("diff", "--name-only", BASE, commit, "--", "src").decode().splitlines()
    need(delta == ([GATE] if mode == "public" else []), "freeze must keep the exact reader and writer closure")
    if mode == "public":
        prior = git("show", f"{BASE}:{GATE}")
        expected = prior.replace(b'if PlanValue.SideMode != "one_sided":',
                                 b'if PlanValue.SideMode not in ("one_sided", "two_sided"):')
        need(prior != expected == git("show", f"{commit}:{GATE}"), "only admit the measured two direction mode")
    need(git("show", f"{commit}:{OWN}") == HERE.read_bytes(), "commit the parity method before freezing")
    need(git("show", f"{WRITER}:{BUILDER}") == git("show", f"{commit}:{BUILDER}"), "author model recipe changed")
    need(digest(git("show", f"{commit}:{MEASURED}")) == MIXED and
         digest(git("show", f"{commit}:{SOURCE_LOCK}")) == LOCK, "pinned cohort evidence")
    source_archive = git("archive", "--format=tar", commit, "src")
    output_archive = BytesIO()
    with open_tar(fileobj=BytesIO(source_archive), mode="r:") as source, open_tar(
        fileobj=output_archive, mode="w:gz"
    ) as target:
        for member in source:
            need(member.isfile() or member.isdir(), "frozen source archive member type")
            target.addfile(member, source.extractfile(member) if member.isfile() else None)
        for name in FILES:
            payload = git("show", f"{commit}:{name}")
            member = TarInfo(name)
            member.mode = 0o644
            member.size = len(payload)
            target.addfile(member, BytesIO(payload))
    packed = output_archive.getvalue()
    folder.mkdir(parents=True)
    with (folder / "Code.tar.gz").open("xb") as file:
        file.write(packed)
    with (folder / HERE.name).open("xb") as file:
        file.write(HERE.read_bytes())
    manifest = {
        "schema": SCHEMA, "mode": mode, "commit": commit,
        "reader_base": BASE, "source_tree": git("rev-parse", f"{commit}:src").decode().strip(),
        "writer_revision": WRITER, "prior_writer_tree": TREE, "mixed_native_receipt_sha256": MIXED,
        "pack_sha256": digest(packed), "method_sha256": digest(HERE.read_bytes()),
        "only_source_delta": delta, "sealed_inputs_read_during_freeze": 0,
    }
    return {"freeze_sha256": publish(folder / "Freeze.json", manifest), "code_source_tree": manifest["source_tree"]}


def warm():
    for name in ("ascii", "utf-8", "utf-8-sig", "utf-16-le", "utf-16-be", "latin-1"):
        codecs.lookup(name)
    for name in (
        "interchange.brep.Validation.BrepValidate", "interchange.document.Behavior.DocumentIo",
        "interchange.document.Models.DocumentProvenance", "interchange.document.Models.DocumentWalk",
        "interchange.document.Validation.AngleRevValidate", "interchange.document.Validation.DocumentAssemblyValidate",
        "interchange.document.Validation.DocumentFeatureValidate", "interchange.document.Validation.DocumentReferenceValidate",
        "interchange.document.Validation.PlaneRevValidate", "interchange.document.Validation.DistExtValidate",
    ):
        import_module(name)


def worker_paths():
    sys.path[:0] = [str(ROOT / "src"), str(HERE.parent), str(ROOT / TOOLS),
                    str(HERE.parent.parent / "PrincipalReader"), str(HERE.parent.parent / "PrincipalWriter")]


def check_result(result, raw, path, doc, strict):
    from convert.adapters.base.TransferContract import TransferMode

    need(result.path == path and result.adapter == FORMAT and result.bytes_written == len(raw), "actual publication receipt")
    need(result.vendor_loadable and result.application_usable and not result.dropped
         and not result.carrier_capabilities and not result.requirements, "native-only write receipt")
    if strict:
        need(doc.capabilities <= result.native_capabilities and
             all(row.mode is TransferMode.KNative for row in result.transfers), "full declared native capability transfers")


def write_worker(request):
    from BuildOrdinaryEndRevolves import inspect_generated, source_model
    from VerifySdkCircleEndRegistration import OutputGuard
    from convert import write_document
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.solidworks.Core.Preparation.Revolve.PrepareRevolve import PrepareRevolve
    from convert.api.ApiContext import GetRegistry

    warm()
    case = request["case"]
    logical, epoch = request["locator"], request["epoch"]
    root = Path(request["scratch"]).resolve()
    normal = root / "Published" / (case["name"] + ".SLDPRT")
    direct_file = root / "Direct" / normal.name
    direct_file.parent.mkdir()
    policy = {"require_native_transfers": True}
    original_options = WriteOptions(values={**policy, "final_destination": logical})
    options = WriteOptions(values={**policy, "final_destination": str(normal)})
    writer = GetRegistry().GetWriter(FORMAT)
    emitter = import_module("convert.adapters.solidworks.Core.Writing.EmitNativeMut")
    emitter.ReadTime = lambda: epoch
    guard = OutputGuard(root, normal.name)
    sys.addaudithook(guard.audit)
    results = []
    with guard.active("memory"):
        doc = source_model(case, logical, epoch)
        prepared = PrepareRevolve(doc, logical, epoch)
        stream = BytesIO()
        need(PrepareRevolve(doc, stream, epoch, original_options).BytesValue == prepared.BytesValue
             and not stream.getvalue(), "frozen path and stream preparation")
        raw = prepared.BytesValue
        need(digest(raw) == request["candidate_sha256"], "exact native-measured candidate bytes")
        audited = inspect_generated(raw, case)
        need(len(audited["streams"]) == 10, "exact load-critical streams")
        if request["mode"] == "staged":
            check_refusal(doc, normal, original_options.values, write_document)
        else:
            for direct in (False, True):
                stream = BytesIO()
                result = (writer.write(doc, stream, original_options) if direct else
                          write_document(doc, stream, destination_format=FORMAT, allow_carrier=False,
                                         values=original_options.values))
                need(stream.getvalue() == raw, "original locator public/direct byte identity")
                check_result(result, raw, None, doc, not direct)
            stream, full_stream = BytesIO(), BytesIO()
            fresh = PrepareRevolve(doc, normal, epoch).BytesValue
            need(len(inspect_generated(fresh, case)["streams"]) == 10, "same fresh locator live owners")
            direct_reply = writer.write(doc, stream, options)
            stream_reply = write_document(doc, full_stream, destination_format=FORMAT, allow_carrier=False,
                                          values=options.values)
            need(stream.getvalue() == full_stream.getvalue() == fresh, "fresh locator memory parity")
    if request["mode"] == "public":
        with guard.active("path"):
            file_reply = writer.write(doc, direct_file, options)
            path_reply = write_document(doc, normal, allow_carrier=False, values=policy)
        need(normal.read_bytes() == direct_file.read_bytes() == fresh
             and tuple(normal.parent.iterdir()) == (normal,), "staged file and direct parity")
        for reply, path, strict in ((direct_reply, None, False), (stream_reply, None, True),
                                    (file_reply, direct_file, False), (path_reply, normal, True)):
            check_result(reply, fresh, path, doc, strict)
            results.append(strict)
    response = {"original_locator_sha256": digest(raw), "exact_streams": 10,
                "public_fresh_locator_routes": len(results), "runtime_input_file_reads": len(guard.denied)}
    if request["mode"] == "public":
        response["fresh_locator_sha256"] = digest(fresh)
        response["native_capabilities"] = sorted(value.value for value in path_reply.native_capabilities)
        response["guarded_output_events"] = dict(guard.events)
    return response


def check_refusal(doc, path, stream_options, write_document):
    from convert.adapters.registry import AdapterNotFoundError

    initial = b"prior stream bytes"
    stream = BytesIO(initial)
    for target, values in ((path, {}), (stream, stream_options or {})):
        try:
            write_document(doc, target, destination_format=FORMAT, allow_carrier=False, values=values)
        except (ValueError, TypeError, AdapterNotFoundError):
            pass
        else:
            raise ValueError("unsupported request published")
    need(not path.exists() and not path.parent.exists() and stream.getvalue() == initial and stream.tell() == 0,
         "rejection must precede output staging")


def negative_worker(request):
    from BuildOrdinaryEndRevolves import source_model
    from VerifySdkCircleEndRegistration import OutputGuard
    from convert import write_document
    from convert.adapters.registry import AdapterNotFoundError
    from convert.api.ApiContext import GetRegistry
    from interchange.geometry.Models.Sketch import ConstraintRef, SketchRelation
    from interchange.geometry.Models.VectorSpace import SpaceVector

    warm()
    GetRegistry().GetWriter(FORMAT)
    root = Path(request["scratch"]).resolve()
    name = request["negative"]
    path = root / "Refused" / ("RevolveRefusal.SLDASM" if name == "foreign-suffix" else "RevolveRefusal.SLDPRT")
    case = {"name": "RevolveRefusal", "plane": "front" if name == "front" else "top", "mode": "two",
            "axis_x_m": 0.003, "axis_axial_m": [-0.011, 0.019], "radius_m": [0.008, 0.022],
            "axial_m": [-0.006, 0.013], "angle_deg": 71.0, "second_deg": 38.0, "edit_angle_deg": 105.0, "reverse": False}
    if name == "mid-plane":
        case["mode"] = "midplane"
    guard = OutputGuard(root, path.name)
    sys.addaudithook(guard.audit)
    with guard.active("memory"):
        doc = source_model(case, r"C:\KitSynthetic\RevolveRefusal.SLDPRT", 1760000000)
        if name in ("equal-halves", "over-turn"):
            first, second = doc.parameters
            value = radians(case["angle_deg"]) if name == "equal-halves" else tau
            doc = replace(doc, parameters=(first, replace(second, value=replace(second.value, value=value))))
            if name == "equal-halves":
                (feature,) = doc.feature_timeline
                doc = replace(doc, feature_timeline=(replace(feature, definition=replace(feature.definition, SideMode="symmetric")),))
        if name == "equal-length":
            (sketch,) = doc.sketches
            relation = SketchRelation("extra-equal-length", "equal", (ConstraintRef("edge/0"), ConstraintRef("edge/2")))
            doc = replace(doc, sketches=(replace(sketch, constraints=sketch.constraints + (relation,)),))
        if name == "translated-support":
            (plane,) = doc.support_planes
            doc = replace(doc, support_planes=(replace(plane, transform=replace(plane.transform, origin=SpaceVector(1, 0, 0))),))
        if name == "without-final":
            stream = BytesIO(b"prior stream bytes")
            try:
                write_document(doc, stream, destination_format=FORMAT, allow_carrier=False)
            except (ValueError, TypeError, AdapterNotFoundError):
                need(stream.getvalue() == b"prior stream bytes" and stream.tell() == 0, "unnamed stream refusal")
            else:
                raise ValueError("unnamed stream unexpectedly emitted")
        else:
            check_refusal(doc, path, {"final_destination": str(path)}, write_document)
    return {"negative": name, "refused_before_publication": True, "runtime_input_file_reads": len(guard.denied)}


def read_worker(request):
    from AuditPrincipalReader import make_guard
    from TwoDirectionReader import strict_history

    warm()
    raw = locked(Path(request["artifact"]), request["artifact_sha256"])
    state, audit = make_guard(ROOT / "src")
    state["enabled"] = True
    result = strict_history(raw, request["case"], request["observed"], cached=request["cached"])
    state["enabled"] = False
    need(not audit["unexpected_attempts"], "guarded source history")
    return result | {"artifact_sha256": request["artifact_sha256"], "unexpected_runtime_artifact_reads": 0,
                     "package_layout_reads": audit["grammar_reads"]}


def worker(request):
    worker_paths()
    return {"write": write_worker, "read": read_worker, "negative": negative_worker}[request["operation"]](request)


def separated(tool, request):
    child = run((sys.executable, "-I", "-B", str(tool), "--worker"), input=json_bytes(request),
                capture_output=True, timeout=150, check=False)
    need(not child.stderr and child.returncode in (0, 1), "fresh proof subprocess")
    result = json.loads(child.stdout)
    need(result.pop("passed") and child.returncode == 0, result.get("predicate", "fresh proof predicate"))
    return result


def process_identity(row):
    identity = row["oracle_identity"]
    need(identity["sha256"] == ORACLE and identity["file_version"] == BUILD and
         identity["pe_machine"] == "0x8664" and identity["version_matches"], "same SP05.2 oracle")
    return identity["process_creation_filetime"]


def controls(native, measured, source_lock):
    result = []
    for label in ("control-before", "control-after"):
        entry = measured[label]
        need(entry["passed"], "healthy recorded bracket")
        current = data(native / (label + ".json"), entry["receipt_sha256"])
        need(current["sha256"] == source_lock["control_sha256"] and
             current["opened"] and current["open_errors"] == current["open_warnings"] == 0 and
             current["rebuilt"] and current["whats_wrong"] == 0 and current["bodies"] > 0 and
             current["mass"]["volume"] > 0 and not current.get("exception") and
             not current["controller_diagnostics"] and not current["dialogs"] and current["features"] and
             all(feature.get("error") == 0 and feature.get("warning") is False
                 for feature in current["features"]), "exact healthy native bracket receipt")
        result.append(process_identity(current))
    return result


def edited_case(case):
    return dict(case, angle_deg=case["edit_angle_deg"], second_deg=case["edit_second_deg"])


def same_angle(value, requested):
    return isclose(value, requested, rel_tol=1e-13, abs_tol=1e-14)


def phase_pair(directory, pins, case):
    need(len(pins) == 2, "two completed native phases")
    first = data(directory / "Initial.json", pins[0])
    last = data(directory / "FreshReopen.json", pins[1])
    after = edited_case(case)
    for row, expected, phase in ((first, case, "reopen"), (last, after, "edited-reopen")):
        need(row["job"] == {"case": expected, "phase": phase}, "native phase seals exact semantic job")
        need(row["passed"] and row["source_immutable"] and row["inspection_completed"] and
             row["open_status"] == {"opened": True, "errors": 0, "warnings": 0}, "clean original and derivative opens")
        need(row["before_explicit_rebuild"]["bodies"] == 1, "nonempty cold native viewport body")
        need(not row["dialogs"] and not row["controller_diagnostics"] and not row["first_failure"], "clean native lifecycle")
    need(first["edit"]["passed"] and first["edited_derivative"]["save_status"] == [True, 0, 0], "clean edited save")
    dimensions = first["edit"]["dimensions"]
    need(len(dimensions) == 2, "two independent angle edits")
    wanted = (
        ("D1", radians(case["angle_deg"]), radians(after["angle_deg"])),
        ("D2", radians(case["second_deg"]), radians(after["second_deg"])),
    )
    for row, (name, initial, final) in zip(dimensions, wanted, strict=True):
        need(row["name"].split("@")[0] == name and row["setter_status"] == 0 and
             same_angle(row["before_radians"], initial) and same_angle(row["after_radians"], final), "actual D1/D2 edit values")
    states = (first["reopened"], first["after-d1"], first["edited"], last["reopened"])
    for state, expected in zip(states, (case, dict(case, angle_deg=after["angle_deg"]), after, after), strict=True):
        need(all(same_angle(value, radians(expected[key])) for value, key in zip(
                 state["angles_radians"], ("angle_deg", "second_deg"), strict=True))
             and state["api_mode"] == 2 and state["reverse"] == case["reverse"]
             and state["bodies"] == 1 and state["profile_relations"] == 4,
             "native driver independence and observation")
        need(len(state["complete_tree"]) == 25 and all(not node["error"] and not node["warning"]
             for node in state["complete_tree"]), "complete healthy native tree")
    need(states[0]["angles_radians"][1] == states[1]["angles_radians"][1] and
         states[1]["angles_radians"][0] == states[2]["angles_radians"][0], "one edit leaves the other recorded driver intact")
    return states, first["edited_derivative"]["sha256"], [process_identity(first), process_identity(last)]


def read_and_compare(tool, name, case, directory, locked_original, row):
    native_path = directory / "Native"
    source, source_edit, source_ids = phase_pair(native_path / (name + "-source"), row["reference_receipt_sha256"], case)
    generated, generated_edit, candidate_ids = phase_pair(native_path / name, row["candidate_receipt_sha256"], case)
    for original, candidate in zip(source, generated, strict=True):
        need(original["complete_tree"] == candidate["complete_tree"]
             and original["body_names"] == candidate["body_names"]
             and original["parents"] == candidate["parents"], "exact paired native tree and body owners")
        first, second = original["mass"], candidate["mass"]
        need(all(format(first[key], ".6g") == format(second[key], ".6g") for key in ("volume", "area", "mass")),
             "six significant native mass measures")
        need(all((abs(a) <= 1e-12 and abs(b) <= 1e-12) or format(a, ".6g") == format(b, ".6g")
                 for a, b in zip(first["com"], second["com"], strict=True)), "six significant signed native centroid")
    phases = (
        ("source-original", locked_original, row["source_sha256"], source[0], case, True),
        ("source-edited", native_path / (name + "-source") / (name + "-edited.SLDPRT"),
         source_edit, source[-1], edited_case(case), True),
        ("candidate-original", directory / "Generated" / (name + ".SLDPRT"),
         row["candidate_sha256"], generated[0], case, False),
        ("candidate-edited", native_path / name / (name + "-edited.SLDPRT"),
         generated_edit, generated[-1], edited_case(case), True),
    )
    proof = {}
    for label, path, sha, observed, intent, cached in phases:
        try:
            proof[label] = separated(tool, {"operation": "read", "artifact": str(path), "artifact_sha256": sha,
                                            "observed": observed, "case": intent, "cached": cached})
        except ParityFailure as error:
            raise ParityFailure(label + " " + str(error)) from None
    return proof, source_ids + candidate_ids


def extract_code(packet, pin, scratch):
    manifest = data(packet / "Freeze.json", pin)
    mode = manifest["mode"]
    need(manifest["schema"] == SCHEMA and mode in MODES and manifest["reader_base"] == BASE and
         manifest["writer_revision"] == WRITER and manifest["prior_writer_tree"] == TREE and
         manifest["mixed_native_receipt_sha256"] == MIXED and manifest["sealed_inputs_read_during_freeze"] == 0,
         "exact frozen parity packet")
    need(manifest["only_source_delta"] == ([GATE] if mode == "public" else []), "isolated public admission delta")
    need(manifest["method_sha256"] == digest(HERE.read_bytes()), "use the frozen proof driver")
    archive = locked(packet / "Code.tar.gz", manifest["pack_sha256"])
    need(not scratch.exists() and scratch.drive.casefold() == "c:", "fresh guest-local proof work directory")
    scratch.mkdir(parents=True)
    source = scratch / "Code"
    with open_tar(fileobj=BytesIO(archive), mode="r:gz") as bundle:
        members = bundle.getmembers()
        names = {row.name.casefold() for row in members}
        need(len(members) == len(names), "duplicate or case aliased archive path")
        need(all((member.isfile() or member.isdir()) and not member.name.startswith("/")
                 and "\\" not in member.name and ":" not in member.name
                 and ".." not in PurePosixPath(member.name).parts
                 and (member.isdir() or member.name.startswith("src/") or member.name in FILES)
                 for member in members), "sealed code archive framing")
        need(set(FILES) <= {member.name for member in members if member.isfile()}, "complete research observer closure")
        bundle.extractall(source, members=members, filter="data")
    tool = source / OWN
    need(digest(tool.read_bytes()) == manifest["method_sha256"], "exact unpacked worker")
    return manifest, source, tool


def verify(args):
    need(os.name == "nt", "replay is restricted to the designated guest")
    need(args.originals.resolve().drive.casefold() == "c:", "native originals must stay in guest custody")
    need(not args.output.exists(), "fresh sanitized receipt destination")
    manifest, source, tool = extract_code(args.packet, args.pin, args.scratch)
    old = data(args.prior_packet / "Freeze.json", OLD_FREEZE)
    need(old["writer_revision"] == WRITER and old["writer_source_tree"] == TREE
         and old["source_lock_sha256"] == LOCK, "prior frozen writer identity")
    private = Path(old["private"])
    need(private.is_absolute() and private.drive.casefold() == "c:", "prior evaluation custody")
    measured = data(args.prior_packet / "NativeReceipt.json", MIXED)
    need(measured == data(source / MEASURED, MIXED), "exact observed mixed receipt")
    need(measured["passed"] is False and measured["heldout_writer_cases_qualified"] == 0 and
         not measured["cases"]["H-Mid-01"]["passed"] and "candidate_receipt_sha256" not in measured["cases"]["H-Mid-01"] and
         measured["cases"]["H-Mid-02"]["passed"] and measured["distinct_processes"] == 15 and
         measured["application_idle"] and measured["controls_unchanged"], "retain issued mixed failure")
    generation = data(private / "Generation.json", GENERATION)
    need(generation["freeze_sha256"] == OLD_FREEZE and generation["writer_source_tree"] == TREE and
         generation["original_native_files_read_during_generation"] == 0, "exact unfitted generation")
    lock = data(source / SOURCE_LOCK, LOCK)
    need(lock["passed"] and lock["distinct_processes"] == 14 and all(lock[label]["passed"]
         for label in ("control-before", "control-after")), "original pre-writer source lock")
    specs = data(args.spec, lock["spec_sha256"])
    need(specs["split"] == "heldout", "actual sealed spec")
    cases = {case["name"]: case for case in specs["cases"] if case["name"] in CASES}
    locked_sources = {row["name"]: row for row in lock["sources"] if row["name"] in CASES}
    need(set(cases) == set(locked_sources) == set(CASES), "exact two selected member identities")
    process_ids = controls(private / "Native", measured, lock)
    result = {}
    for slot, name in enumerate(CASES, 1):
        case = cases[name]
        row = measured["cases"][name]
        original = args.originals / name / (name + ".SLDPRT")
        need(case["mode"] == "two" and locked_sources[name]["mode"] == "two" and row["passed"] and
             row["source_sha256"] == locked_sources[name]["native_sha256"], "real independently qualified two-sense member")
        need(generation["cases"][name]["candidate_sha256"] == row["candidate_sha256"] and
             row["runtime_external_access_attempts"] == 0 and row["exact_streams"] == 10,
             "generated member provenance")
        target = args.scratch / f"Output{slot:02}"
        target.mkdir()
        writing = separated(tool, {"operation": "write", "mode": manifest["mode"], "case": case,
                                   "locator": str(private / "Generated" / (name + ".SLDPRT")),
                                   "epoch": int(old["frozen_at"]), "candidate_sha256": row["candidate_sha256"],
                                   "scratch": str(target)})
        readings, identities = read_and_compare(tool, name, case, private, original, row)
        process_ids += identities
        result[f"Pair{slot:02}"] = {"generation": writing, "strict_histories": readings,
                                   "source_native_receipts": row["reference_receipt_sha256"],
                                   "candidate_native_receipts": row["candidate_receipt_sha256"],
                                   "paired_native_tree_rows_per_phase": 25,
                                   "paired_native_mass_checks": 24}
    need(len(set(process_ids)) == len(process_ids) == 10 and
         all(process_ids[0] < stamp < process_ids[1] for stamp in process_ids[2:]), "native cycles inside healthy controls")
    negative_results = []
    for idx, name in enumerate(REFUSALS):
        folder = args.scratch / f"Refusal{idx:02}"
        folder.mkdir()
        negative_results.append(separated(tool, {"operation": "negative", "negative": name, "scratch": str(folder)}))
    result = {"schema": SCHEMA, "mode": manifest["mode"], "verified_two_direction_pairs": 2,
              "mixed_batch": {"sha256": MIXED, "passed": False, "original_qualified_count": 0},
              "freeze_sha256": args.pin, "source_commit": manifest["commit"],
              "source_tree": manifest["source_tree"], "writer_revision": WRITER,
              "new_native_processes": 0, "prior_distinct_processes_verified": 10,
              "negative_public_cases": negative_results, "pairs": result, "passed": True}
    return {"passed": True, "mode": manifest["mode"], "receipt_sha256": publish(args.output, result)}


def failure(error):
    result = {"passed": False, "error_type": type(error).__name__}
    if type(error).__name__ == "ParityFailure":
        result["predicate"] = str(error)
    return result


def main():
    parser = ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--freeze", type=Path)
    parser.add_argument("--mode", choices=MODES, default="staged")
    parser.add_argument("--packet", type=Path)
    parser.add_argument("--pin")
    parser.add_argument("--prior-packet", type=Path)
    parser.add_argument("--originals", type=Path)
    parser.add_argument("--spec", type=Path)
    parser.add_argument("--scratch", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.freeze:
        outcome = freeze(args.freeze, args.mode)
    elif args.worker:
        try:
            outcome = worker(json.load(sys.stdin)) | {"passed": True}
        except Exception as error:
            outcome = failure(error)
    else:
        try:
            outcome = verify(args)
        except Exception as error:
            outcome = failure(error)
    print(json.dumps(outcome, sort_keys=True, allow_nan=False))
    return int(outcome.get("passed") is False)


if __name__ == "__main__":
    raise SystemExit(main())
