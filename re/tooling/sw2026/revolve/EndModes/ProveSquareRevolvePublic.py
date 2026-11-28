from argparse import ArgumentParser
from dataclasses import replace
from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path, PurePosixPath
from subprocess import check_output, run
import sys
import time
from zipfile import ZIP_DEFLATED, ZipFile


HERE = Path(__file__).resolve()
ROOT = HERE.parents[5] if len(HERE.parents) > 5 else None
sys.path.insert(0, str(HERE.parent))

BASE = "60fba91607773d6d0b9c5449a047caaa11c1e0ab"
SCHEMA = "kit.sw2026.square-revolve-public-parity.v1"
TOOLS = "re/tooling/sw2026/"
RV = TOOLS + "revolve/"
END = RV + "EndModes/"
SELF = END + HERE.name
GATE = "src/convert/adapters/solidworks/Core/Preparation/Revolve/PlanPublicRevolve.py"
REFUSALS = ("missing-equal", "plain-two", "one-sided-equal", "opposite", "axis-operand", "non-square", "duplicated",
            "front", "translated-support", "whole-turn", "foreign-suffix", "without-final")
SHARED = (END + "ProveTwoDirectionRevolves.py",)
GEOMETRY = (END + "BuildOrdinaryEndRevolves.py", END + "BuildSquareRevolves.py", END + "ProjectSquareSource.py",
            END + "SquareEdgeRoles.py")


class ProofFailure(ValueError):
    pass


def need(value, check):
    if not value:
        raise ProofFailure(check)


def digest(raw):
    return sha256(raw).hexdigest()


def locked(path, wanted):
    raw = path.read_bytes()
    need(digest(raw) == wanted, "sealed square parity digest")
    return raw


def data(path, wanted):
    return json.loads(locked(path, wanted))


def json_bytes(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def publish(path, value):
    raw = json_bytes(value)
    with path.open("xb") as stream:
        stream.write(raw)
    return digest(raw)


def freeze(output):
    from ProveTwoDirectionRevolves import FILES
    from SquarePublicNativeInputs import LOCK_REV, LOCK_SHA, NATIVE, NATIVE_SHA, PRELOCK, WRITER, WRITER_TREE

    def git(*args):
        return check_output(("git", "-C", str(ROOT), *args))

    revision = git("rev-parse", "HEAD").decode().strip()
    source_tree = git("rev-parse", "HEAD:src").decode().strip()
    need(not output.exists() and not output.is_relative_to(ROOT), "fresh freeze outside the source tree")
    need(git("diff", "--name-only", BASE, revision, "--", "src").decode().splitlines() == [GATE],
         "the public admission is the only changed production file")
    before = git("show", f"{BASE}:{GATE}")
    expected = before.replace(b'if PlanValue.SideMode != "one_sided":',
                              b'if PlanValue.EqualRule is None and PlanValue.SideMode != "one_sided":').replace(
        b"if PlanValue.EqualRule is not None:\n",
        b'if PlanValue.EqualRule is not None and PlanValue.SideMode not in (\n        "symmetric_full",\n        "two_sided",\n    ):\n')
    need(before != expected == git("show", f"{revision}:{GATE}"), "admit only the measured square end modes")
    git("merge-base", "--is-ancestor", LOCK_REV, WRITER)
    git("merge-base", "--is-ancestor", WRITER, BASE)
    need(git("rev-parse", f"{WRITER}:src").decode().strip() == WRITER_TREE
         and all(git("show", f"{WRITER}:{name}") == git("show", f"{revision}:{name}") for name in GEOMETRY)
         and git("show", f"{revision}:{SELF}") == HERE.read_bytes(), "exact published neutral projection and generation methods")
    measured, lock = (git("show", f"{revision}:{name}") for name in (NATIVE, PRELOCK))
    need(digest(measured) == NATIVE_SHA and digest(lock) == LOCK_SHA
         and json.loads(lock)["finished_at"] < int(git("show", "-s", "--format=%ct", WRITER)),
         "the recorded source lock predates square construction")
    files = ((set(FILES) - {name for name in FILES if name.endswith(".json")}) | set(GEOMETRY) | set(SHARED)
             | {SELF, END + "AuditEqualLengthRows.py", END + "SquarePublicNativeInputs.py", END + "ReadPublicSquareRevolve.py", NATIVE, PRELOCK})
    buffer = BytesIO()
    with ZipFile(BytesIO(git("archive", "--format=zip", revision, "src"))) as source:
        with ZipFile(buffer, mode="w", compression=ZIP_DEFLATED, compresslevel=6) as target:
            for item in source.namelist():
                if not item.endswith("/"):
                    target.writestr(item, source.read(item))
            for name in sorted(files):
                target.writestr(name, git("show", f"{revision}:{name}"))
    output.mkdir()
    raw = buffer.getvalue()
    with (output / "Code.zip").open("xb") as file:
        file.write(raw)
    with (output / HERE.name).open("xb") as file:
        file.write(HERE.read_bytes())
    pin = publish(output / "Freeze.json", {"schema": SCHEMA, "base": BASE, "source_commit": revision,
        "source_tree": source_tree, "prior_writer_revision": WRITER, "prior_writer_src_tree": WRITER_TREE,
        "pre_writer_lock_sha256": LOCK_SHA, "native_evidence_sha256": NATIVE_SHA, "source_delta": [GATE],
        "archive_sha256": digest(raw), "tool_sha256": digest(HERE.read_bytes()), "research_files": sorted(files),
        "host_heldout_input_reads": 0, "frozen_at": time.time()})
    return {"freeze_sha256": pin, "source_tree": source_tree}


def extract(packet, pin, scratch):
    manifest = data(packet / "Freeze.json", pin)
    need(manifest["schema"] == SCHEMA and manifest["base"] == BASE and manifest["source_delta"] == [GATE]
         and manifest["host_heldout_input_reads"] == 0 and digest(HERE.read_bytes()) == manifest["tool_sha256"],
         "exact frozen public square packet")
    code = scratch / "Code"
    scratch.mkdir()
    with ZipFile(BytesIO(locked(packet / "Code.zip", manifest["archive_sha256"]))) as archive:
        paths = archive.namelist()
        need(len(paths) == len({path.casefold() for path in paths})
             and all(not path.startswith("/") and ":" not in path and "\\" not in path
                     and ".." not in PurePosixPath(path).parts for path in paths)
             and {path for path in paths if not path.startswith("src/")} == set(manifest["research_files"]),
             "archive framing and exact independent research closure")
        archive.extractall(code)
    entry = code / SELF
    locked(entry, manifest["tool_sha256"])
    return manifest, code, entry


def public_paths(root):
    sys.path[:0] = [str(root / "src"), str(root / TOOLS), str(root / END),
                    str(root / (RV + "PrincipalReader")), str(root / (RV + "PrincipalWriter"))]


def synthetic_case():
    return {"name": "SquarePublicScope", "plane": "top", "mode": "midplane", "axis_x_m": .003,
            "axis_axial_m": [-.011, .019], "radius_m": [.008, .022], "axial_m": [-.006, .008],
            "angle_deg": 71.0, "second_deg": 0.0, "edit_angle_deg": 124.0, "edit_second_deg": 0.0,
            "reverse": False, "equal_edges": [1, 0]}


def negative(request):
    from BuildOrdinaryEndRevolves import source_model
    from ProveTwoDirectionRevolves import FORMAT, check_refusal, warm
    from VerifySdkCircleEndRegistration import OutputGuard
    from convert import write_document
    from convert.adapters.registry import AdapterNotFoundError
    from convert.adapters.solidworks.Core.Preparation.Revolve.PlanPublicRevolve import PlanPublicRevolve
    from convert.api.ApiContext import GetRegistry
    from interchange.geometry.Models.Sketch import ConstraintRef
    from interchange.geometry.Models.VectorSpace import SpaceVector

    warm()
    writer = GetRegistry().GetWriter(FORMAT)
    kind = request["negative"]
    case = synthetic_case()
    if kind in ("missing-equal", "plain-two"):
        case.pop("equal_edges")
    if kind == "plain-two":
        case.update(mode="two", second_deg=32.0, edit_second_deg=41.0)
    if kind == "one-sided-equal":
        case["mode"] = "single"
    if kind == "opposite":
        case["equal_edges"] = [0, 2]
    if kind == "non-square":
        case["axial_m"] = [-.006, .013]
    if kind == "front":
        case["plane"] = "front"
    if kind == "whole-turn":
        case["angle_deg"] = 360.0
    root = Path(request["scratch"]).resolve()
    destination = root / "Absent" / (case["name"] + (".SLDASM" if kind == "foreign-suffix" else ".SLDPRT"))
    existing = root / "Existing" / destination.name
    existing.parent.mkdir()
    prior = b"previous bytes"
    existing.write_bytes(prior)
    guard = OutputGuard(root, destination.name)
    sys.addaudithook(guard.audit)
    refusal = None
    with guard.active("memory"):
        doc = source_model(case, r"C:\KitSynthetic\SquarePublicScope.SLDPRT", 1760000000)
        if kind in ("axis-operand", "duplicated"):
            sketch, = doc.sketches
            relation = sketch.constraints[-1]
            rules = sketch.constraints
            if kind == "axis-operand":
                axis, = (value for value in sketch.entities if value.construction)
                rules = (*rules[:-1], replace(relation, references=(relation.references[0], ConstraintRef(axis.id))))
            else:
                rules += (replace(relation, id="relation/repeated-equal"),)
            doc = replace(doc, sketches=(replace(sketch, constraints=rules),))
        if kind == "translated-support":
            plane, = doc.support_planes
            doc = replace(doc, support_planes=(replace(plane, transform=replace(plane.transform, origin=SpaceVector(1, 0, 0))),))
        if kind in ("without-final", "foreign-suffix"):
            need(PlanPublicRevolve(doc) is not None, "destination contrast must use a qualified square")
        else:
            try:
                PlanPublicRevolve(doc)
            except ValueError as error:
                refusal = str(error)
            else:
                raise ValueError("unqualified square reached the public planner")
        if kind != "without-final":
            check_refusal(doc, destination, {"final_destination": str(destination)}, write_document)
            try:
                write_document(doc, existing, destination_format=FORMAT, allow_carrier=False, overwrite=True)
            except (ValueError, TypeError, AdapterNotFoundError):
                pass
            else:
                raise ValueError("unqualified publication tried to replace an existing destination")
        for direct in (True, False):
            memory = BytesIO(prior)
            try:
                if direct:
                    writer.write(doc, memory, None)
                else:
                    write_document(doc, memory, destination_format=FORMAT, allow_carrier=False)
            except (ValueError, TypeError, AdapterNotFoundError):
                need(memory.getvalue() == prior and memory.tell() == 0, "stream changed before refusal")
            else:
                raise ValueError("unqualified scope or unnamed stream published")
    need(tuple(existing.parent.iterdir()) == (existing,) and existing.read_bytes() == prior,
         "refusal changed prior bytes or left staging files")
    return {"case": kind, "planner_refusal": refusal, "publication_refused": True, "runtime_input_file_reads": len(guard.denied)}


def worker(request):
    started = time.monotonic_ns()
    public_paths(ROOT)
    from ProveTwoDirectionRevolves import warm, write_worker

    def no_runtime(event, args):
        if event.startswith(("socket.", "ctypes.", "subprocess.")) or event in ("os.system", "os.fork", "os.exec", "os.posix_spawn"):
            raise PermissionError("public square process crossed the CAD or external execution boundary")

    sys.addaudithook(no_runtime)
    operation = request["operation"]
    if operation == "negative":
        result = negative(request)
    elif operation == "write":
        result = write_worker(request)
    elif operation == "read":
        from AuditPrincipalReader import make_guard
        from ReadPublicSquareRevolve import strict_square

        warm()
        raw = locked(Path(request["path"]), request["sha256"])
        state, evidence = make_guard(ROOT / "src")
        state["enabled"] = True
        result = strict_square(raw, request["case"], request["observation"], request["cached"])
        need(not evidence["unexpected_attempts"], "strict reader file and runtime input boundary")
        result |= {"package_grammar_reads": evidence["grammar_reads"], "runtime_external_reads": 0}
    else:
        raise ValueError("unknown parity worker mode")
    need(not any(name in ("Swapp", "pythoncom", "pywintypes") or name.startswith("win32com") for name in sys.modules),
         "parity worker imported a CAD runtime")
    return result | {"passed": True, "process": [os.getpid(), started]}


def isolated(entry, request):
    child = run((sys.executable, "-I", "-B", str(entry), "--worker"), input=json_bytes(request),
                capture_output=True, timeout=150, check=False)
    need(not child.stderr and child.returncode in (0, 1), "fresh isolated Windows Python worker")
    result = json.loads(child.stdout)
    if not result.pop("passed"):
        raise RuntimeError(f"{request['operation']}::" + result.get("predicate", result["error_type"]))
    need(child.returncode == 0, "guarded worker exit status")
    return result


def verify(args):
    need(os.name == "nt" and args.scratch.drive.casefold() == "c:" and not args.output.exists()
         and args.output.parent == args.packet, "guest-only proof with fresh private work and sanitized shared receipt")
    manifest, code, entry = extract(args.packet, args.pin, args.scratch)
    sys.path.insert(0, str(entry.parent))
    from SquarePublicNativeInputs import LOCK_SHA, NATIVE_SHA, WRITER, WRITER_TREE, authorized_inputs, edited_case

    need(manifest["prior_writer_revision"] == WRITER and manifest["prior_writer_src_tree"] == WRITER_TREE
         and manifest["pre_writer_lock_sha256"] == LOCK_SHA and manifest["native_evidence_sha256"] == NATIVE_SHA,
         "exact prior square writer and pre-implementation lock evidence")
    authorized = authorized_inputs(code)
    pairs, workers = [], []
    for index, (case, epoch, candidate, candidate_sha, derivative, saved_sha, observed) in enumerate(authorized, 1):
        folder = args.scratch / f"Pair{index:02}"
        folder.mkdir()
        result = isolated(entry, {"operation": "write", "mode": "public", "case": case, "locator": str(candidate),
                                  "epoch": epoch, "candidate_sha256": candidate_sha, "scratch": str(folder)})
        workers.append(tuple(result.pop("process")))
        need(result["public_fresh_locator_routes"] == 4 and result["exact_streams"] == 10
             and result["original_locator_sha256"] == candidate_sha and not result["runtime_input_file_reads"],
             "direct and registry publication must reproduce exact measured bytes")
        reads = {}
        for label, path, pin, intent, state, cached in (
            ("measured_generated", candidate, candidate_sha, case, observed["reopened"], False),
            ("registry_generated", folder / "Published" / candidate.name, result["fresh_locator_sha256"], case, observed["reopened"], False),
            ("native_saved_edit", derivative, saved_sha, edited_case(case), observed["edited_fresh_reopen"], True)):
            proof = isolated(entry, {"operation": "read", "path": str(path), "sha256": pin, "case": intent,
                                     "observation": state, "cached": cached})
            workers.append(tuple(proof.pop("process")))
            reads[label] = proof
        pairs.append({"mode": case["mode"], "verified_native_states": len(observed), "generation": result, "strict_reads": reads})
    negatives = []
    for index, label in enumerate(REFUSALS, 1):
        folder = args.scratch / f"Refusal{index:02}"
        folder.mkdir()
        reply = isolated(entry, {"operation": "negative", "negative": label, "scratch": str(folder)})
        workers.append(tuple(reply.pop("process")))
        negatives.append(reply)
    need(len(workers) == len(set(workers)), "proof processes must be independent")
    receipt = {"schema": SCHEMA, "source_commit": manifest["source_commit"], "source_tree": manifest["source_tree"],
               "freeze_sha256": args.pin, "prior_native_receipt_sha256": NATIVE_SHA, "previous_native_processes_verified": 10,
               "previous_heldout_cases_matched": 2, "new_heldout_credit": 0, "new_native_processes": 0,
               "native_source_files_read": 0, "guarded_workers": len(workers), "pairs": pairs, "writer_refusals": negatives,
               "passed": True}
    return {"passed": True, "receipt_sha256": publish(args.output, receipt)}


def main():
    parser = ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--freeze", type=Path)
    parser.add_argument("--packet", type=Path)
    parser.add_argument("--pin")
    parser.add_argument("--scratch", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.freeze:
        result = freeze(args.freeze.resolve())
    elif args.worker:
        result = worker(json.load(sys.stdin))
    else:
        result = verify(args)
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        allowed = type(error) in (ProofFailure, RuntimeError, PermissionError) or type(error).__name__ == "ParityFailure"
        report = {"passed": False, "error_type": type(error).__name__}
        if allowed:
            report["predicate"] = str(error)
        if isinstance(error, OSError):
            report.update({key: getattr(error, key) for key in ("errno", "winerror") if type(getattr(error, key, None)) is int})
        print(json.dumps(report, sort_keys=True))
        raise SystemExit(1)
