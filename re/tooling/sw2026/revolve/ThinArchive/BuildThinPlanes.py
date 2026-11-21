from argparse import ArgumentParser
from base64 import b64decode, b64encode
from dataclasses import replace
from importlib import import_module
from io import BytesIO
import json
from pathlib import Path, PureWindowsPath
from subprocess import check_output, run
import sys

from BuildThinControls import HERE, LOCK_PATH, LOCK_SHA256, PREWRITER_LOCK, ROOT, encode
from AuditThinArchive import phase, checked_bytes, refusal
from AuditRevEndOwners import digest, guard_runtime, require
from AuthorRevolveFamilies import ORACLE, TOOLS
from RevolveFamilyModel import edited_case, validate_specs, world
from RunThinNative import PLANE_SCHEMA
from ThinNeutral import make_model
from ThinPlaneAudit import measure_plane

from convert import write_document
from convert.adapters.registry import AdapterNotFoundError
from convert.adapters.solidworks.Container.Format import KeywordsStream
from convert.adapters.solidworks.Core.Adapter import KFormatId
from convert.adapters.solidworks.Core.Preparation.PlanNativePart import PlanNativePart
from convert.adapters.solidworks.Core.Preparation.Revolve.PrepareRevolve import PrepareRevolve
from interchange.Features.ThinRevolve import ThinRevolve
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.serialization.Deserialize import FromData
from interchange.serialization.EncodeData import ToData


SOURCE = "7475170f6f524ba33fe826b54976f7d2793c9bd603851d1a31866220d26c6253"
SPEC = "72341240e566c2fe027716478fa3e07b389cf4e5451e463f3c14698afe23e694"
DISCLOSED = "cdada047b9f9bd7be97b62383c07bcee06a527a69152af83d932801e2a556b5c"
WALL_MODES = {"one": "one_sided", "opposite": "opposite", "midplane": "midplane", "two": "two_sided"}
PUBLIC_REFUSAL = "public native thin revolve requires independent native acceptance"


def portable(case):
    doc = make_model(case)
    (plane,), (feature,) = doc.support_planes, doc.feature_timeline
    axes = ([0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1])
    plane = replace(plane, name=case["plane"].title() + " Plane",
                    transform=Transform(*(SpaceVector(*world(case, axis)) for axis in axes)))
    arc = feature.definition
    arc = replace(arc, AxisOrigin=SpaceVector(*world(case, (arc.AxisOrigin.x, arc.AxisOrigin.y, 0))),
                  AxisDirection=SpaceVector(*world(case, (0, -1 if case["reverse"] else 1, 0))))
    definition = ThinRevolve(arc, WALL_MODES[case["wall_mode"]], *feature.parameter_ids[1:])
    return replace(doc, support_planes=(plane,), feature_timeline=(replace(feature, definition=definition),))


def worker(case, destination, epoch):
    for name in ("DocumentProvenance", "AngleRevValidate", "DocumentAssemblyValidate",
                 "DocumentFeatureValidate", "DocumentReferenceValidate", "PlaneRevValidate", "DistExtValidate"):
        package = "Models" if name == "DocumentProvenance" else "Validation"
        import_module(f"interchange.document.{package}.{name}")
    doc = portable(case)
    decoded = FromData(ToData(doc))
    require(decoded == doc, "portable thin definition lost its driver references")
    edited = portable(edited_case(case))
    (sketch,) = doc.sketches
    suppressed = replace(doc, sketches=(replace(sketch, suppressed=True),))
    reversed_doc = portable(dict(case, reverse=True))
    blocked = guard_runtime()
    for target in (doc, decoded, edited, suppressed, reversed_doc):
        target.assert_valid()
    part = PrepareRevolve(decoded, destination, epoch)
    require(part.BytesValue == PrepareRevolve(doc, destination, epoch).BytesValue,
            "principal thin bytes differ after neutral serialization")
    proof = measure_plane(part.BytesValue, case)
    edit_bytes = PrepareRevolve(edited, destination, epoch).BytesValue
    changed = measure_plane(edit_bytes, edited_case(case))
    require([name for name in proof["typed_streams"] if proof["typed_streams"][name] != changed["typed_streams"][name]]
            == ["Contents/Config-0-ResolvedFeatures", KeywordsStream],
            "independent thin angle and wall edits affected unexpected streams")
    plan_refusal = refusal(lambda: PlanNativePart(doc), PUBLIC_REFUSAL)
    destination_stream = BytesIO()
    try:
        write_document(doc, destination_stream, destination_format=KFormatId, allow_carrier=False,
                       values={"final_destination": destination})
    except AdapterNotFoundError as error:
        require(not destination_stream.getvalue() and destination_stream.tell() == 0, "public thin refusal emitted native data")
        public_refusal = type(error).__name__
    else:
        raise ValueError("public writer admitted an independent unqualified thin profile")
    refusals = {"public_plan": plan_refusal, "public_stream": public_refusal,
                "suppressed_sketch": refusal(lambda: PrepareRevolve(suppressed, destination, epoch), "open lines"),
                "reverse_axis": refusal(lambda: PrepareRevolve(reversed_doc, destination, epoch), "forward ordered axis")}
    require(not blocked, "principal thin builder attempted external input access")
    return {**proof, "edited_model_sha256": changed["sha256"], "portable_round_trip": True,
            "refusals": refusals, "writer_external_access_attempts": 0,
            "candidate": b64encode(part.BytesValue).decode("ascii")}


def build_case(case, locator, epoch):
    request = {"case": case, "destination": locator, "epoch": epoch}
    output = run((sys.executable, "-B", __file__, "--worker"), input=encode(request), capture_output=True)
    require(output.returncode == 0, output.stderr.decode())
    proof = json.loads(output.stdout)
    candidate = b64decode(proof.pop("candidate"), validate=True)
    require(proof["sha256"] == digest(candidate), "principal thin worker digest differs")
    return candidate, proof


def source_controls(capture, cases, lock):
    result, proof = {}, {}
    for case, row in zip(cases, lock["sources"], strict=True):
        name = case["name"]
        require(row["case"] == name and row["passed"] and case["first_wall_sign"] in (None, 1),
                "principal disclosed source roles differ")
        authored, reopened, rereopened = (phase(capture, name, info) for info in row["phases"])
        original = checked_bytes(capture / name / (name + ".SLDPRT"), row["native_sha256"])
        edited = checked_bytes(capture / name / (name + "-edited.SLDPRT"), reopened["edited_derivative"]["sha256"])
        require(authored["native_sha256"] == row["native_sha256"], "principal source lost original provenance")
        proof[name] = {"original": measure_plane(original, case, reopened["reopened"]),
                       "edited": measure_plane(edited, edited_case(case), rereopened["reopened"])}
        result[f"Sources/{name}.SLDPRT"] = original
        for relative, info in zip((name + ".reopen.json", name + "-edited.edited-reopen.json"), row["phases"][1:], strict=True):
            result[f"References/{relative}"] = checked_bytes(capture / name / relative, info["sha256"])
    return result, proof


def reports_before_generation(args):
    source = checked_bytes(args.capture / "SourceLock.json", SOURCE)
    lock = json.loads(source)
    spec = checked_bytes(args.spec, SPEC)
    cases = validate_specs(json.loads(spec))
    require(lock["passed"] and lock["oracle_sha256"] == ORACLE and lock["oracle_build"] == "34.5.2.0604"
            and lock["fresh_processes"] == lock["distinct_processes"] == 8 and lock["idle_after"]
            and lock["control-before"]["passed"] and lock["control-after"]["passed"]
            and lock["spec_sha256"] == SPEC and lock["split"] == "discovery" and lock["family"] == "thin"
            and tuple((case["plane"], case["wall_mode"], case["reverse"]) for case in cases)
            == (("top", "opposite", False), ("right", "midplane", False)),
            "principal discovery identities do not match the already measured sources")
    controls = {"ModelSpec.json": spec, "SourceLock.json": source,
                "Control.SLDPRT": checked_bytes(args.front / "Packet" / "Control.SLDPRT", lock["control_sha256"])}
    known = json.loads(checked_bytes(args.front / "NativeResult.json", DISCLOSED))
    require(known["passed"] and known["distinct_processes"] == 18, "the original four Front native parents are unproved")
    return controls, lock, cases


def stage(args):
    require(args.guest.is_absolute() and args.guest.drive.casefold() == "c:" and not args.output.exists()
            and not args.output.resolve().is_relative_to(ROOT), "use a new external packet and absolute C-drive target")
    require(not check_output(("git", "status", "--porcelain", "--untracked-files=no"), cwd=ROOT).strip()
            and run(("git", "merge-base", "--is-ancestor", PREWRITER_LOCK, "HEAD"), cwd=ROOT).returncode == 0
            and digest((ROOT / LOCK_PATH).read_bytes()) == LOCK_SHA256, "freeze a clean writer after the prewriter source lock")
    contents, lock, cases = reports_before_generation(args)
    sources, typed_sources = source_controls(args.capture, cases, lock)
    contents.update(sources)
    for name in TOOLS:
        contents["Tools/" + name] = checked_bytes(args.spec.parent / name, lock["tool_sha256"][name])
    for name in ("RunThinNative.py", "CompareThinNative.py"):
        contents["Tools/" + name] = (HERE / name).read_bytes()
    frozen_front = args.front / "Packet"
    front_receipt = json.loads((frozen_front / "BuildReceipt.json").read_bytes())
    front_rows = json.loads((args.front / "NativeResult.json").read_bytes())["cases"]
    front_cases = validate_specs(json.loads(checked_bytes(frozen_front / "ModelSpec.json", front_receipt["model_spec_sha256"])))
    front_proof = {}
    for case, reference in zip(front_cases, front_rows, strict=True):
        name = case["name"]
        native = PureWindowsPath(front_receipt["logical_candidate_directory"]) / (name + ".SLDPRT")
        candidate, proof = build_case(case, str(native), front_receipt["epoch"])
        exact = checked_bytes(frozen_front / "Candidates" / native.name, reference["candidate_sha256"])
        require(candidate == exact and reference["case"] == name, "shared constructor drifted from the exact native-tested Front output")
        front_proof[name] = proof
    rows = {}
    for case in cases:
        name = case["name"]
        locator = str(args.guest / "Candidates" / (name + ".SLDPRT"))
        raw, row = build_case(case, locator, args.epoch)
        repeat, second = build_case(case, locator, args.epoch)
        require(raw == repeat and row == second, "principal thin fresh-process bytes differ")
        rows[name] = row
        contents["Candidates/" + name + ".SLDPRT"] = raw
    revision, tree = (check_output(("git", "rev-parse", target), cwd=ROOT, text=True).strip()
                      for target in ("HEAD", "HEAD:src"))
    contents["BuildReceipt.json"] = encode({"writer_revision": revision, "writer_sdk_tree": tree, "spec_sha256": SPEC,
        "source_lock_sha256": SOURCE, "front_native_result_sha256": DISCLOSED, "prewriter_lock_sha256": LOCK_SHA256,
        "rows": rows, "front_exact_parity": front_proof, "typed_disclosed_sources": typed_sources,
        "writer_processes": 8, "common_epoch": args.epoch, "public_writer": False, "native_acceptance": False})
    job = {"schema": PLANE_SCHEMA, "logical_root": str(args.guest), "oracle_sha256": ORACLE, "source_lock_sha256": SOURCE,
           "writer_revision": revision, "writer_sdk_tree": tree, "files": {name: digest(raw) for name, raw in contents.items()}}
    contents["NativeJob.json"] = encode(job)
    args.output.mkdir(parents=True)
    for name, raw in contents.items():
        path = args.output / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(raw)
    print(json.dumps({"job_sha256": digest(contents["NativeJob.json"]), "build_receipt_sha256": digest(contents["BuildReceipt.json"]),
                       "native_processes": 10, "cases": {name: row["sha256"] for name, row in rows.items()}}))


if __name__ == "__main__":
    parser = ArgumentParser()
    for name in ("capture", "spec", "front", "output"):
        parser.add_argument("--" + name, type=Path)
    parser.add_argument("--guest", type=PureWindowsPath)
    parser.add_argument("--epoch", type=int, default=1760000000)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    if args.worker:
        sys.stdout.buffer.write(encode(worker(**json.load(sys.stdin))))
    else:
        stage(args)
