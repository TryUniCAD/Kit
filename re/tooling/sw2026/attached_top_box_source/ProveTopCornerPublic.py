from argparse import ArgumentParser
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from io import BytesIO
import json
import os
from pathlib import Path, PurePosixPath
from subprocess import run
import sys
from zipfile import ZipFile


HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
TOOLS = "re/tooling/sw2026/"
ENTRY = TOOLS + "attached_top_box_source/" + HERE.name
FORMAT = "solidworks.sldprt"
SCHEMA = "kit.sw2026.public-top-corner-parity.v1"
PRIOR_JOB = "cb10b3182e31b8480a393bb9f0fca7a08ec8be5a49a942779440df76f4de9f83"
PRIOR_RESULT = "21e671183cc6caf6b5c801e7de38f847d58f3bf2a299385e9abf4fe35a953189"
LOCK_REVISION = "e7bedf0df32d2e0b6defae065766b37f90a60e0f"
SLOTS = ("Slot01", "Slot02")
NEGATIVES = ("coordinates-only", "wrong-corner", "free-datum", "suppressed")
PROJECTOR = TOOLS + "attached_top_box_source/ProjectNativeAttachedTopBox.py"


def digest(raw):
    return sha256(raw).hexdigest()


def payload(path, expected):
    raw = path.read_bytes()
    if digest(raw) != expected:
        raise ValueError("frozen file digest differs: " + path.name)
    return raw


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def publish(path, raw):
    with path.open("xb") as stream:
        stream.write(raw)
    return digest(raw)


def unpack(raw, target):
    target.mkdir()
    with ZipFile(BytesIO(raw)) as archive:
        names = archive.namelist()
        assert len(names) == len({name.casefold() for name in names})
        assert all(not name.startswith("/") and ":" not in name and "\\" not in name
                   and ".." not in PurePosixPath(name).parts for name in names)
        archive.extractall(target)


def external_anchor(document, variant=None):
    from interchange.Enums.EnumGeometry import GeometryKind
    from interchange.geometry.Models.GeometryCurves import PointGeometry
    from interchange.geometry.Models.Sketch import ConstraintRef, SketchEntity, SketchRelation
    from interchange.geometry.Models.VectorPlane import PlaneVector

    if variant == "coordinates-only":
        return document
    (sketch,) = document.sketches
    (contour,) = sketch.closed_profile_entity_ids
    origin = SketchEntity("anchor:model-origin", GeometryKind.KPoint, PointGeometry(PlaneVector(0.0, 0.0)),
                          construction=True, fixed=variant != "free-datum")
    coincidence = SketchRelation("anchor:coincidence", "coincident",
                                 (ConstraintRef(origin.id), ConstraintRef(contour[0], "end" if variant == "wrong-corner" else "start")),
                                 suppressed=variant == "suppressed")
    return replace(document, sketches=(replace(sketch, entities=(*sketch.entities, origin),
                                                constraints=(*sketch.constraints, coincidence)),))


def warm():
    for name in ("ascii", "utf-8", "utf-8-sig", "utf-16-le", "utf-16-be", "latin-1"):
        lookup(name)
    for name in ("interchange.brep.Validation.BrepValidate", "interchange.document.Behavior.DocumentIo",
                 "interchange.document.Models.DocumentProvenance", "interchange.document.Models.DocumentWalk",
                 "interchange.document.Validation.AngleRevValidate", "interchange.document.Validation.DistExtValidate",
                 "interchange.document.Validation.DocumentAssemblyValidate", "interchange.document.Validation.DocumentFeatureValidate",
                 "interchange.document.Validation.DocumentReferenceValidate", "interchange.document.Validation.PlaneRevValidate"):
        import_module(name)


def check_reply(result, raw, path, document, registry):
    assert result.path == path and result.adapter == FORMAT and result.bytes_written == len(raw)
    assert result.application_usable and result.vendor_loadable and not result.dropped and not result.carrier_capabilities
    if registry:
        assert document.capabilities <= result.native_capabilities
        assert all(item.mode.value == "native" for item in result.transfers)


def worker(request, scratch, variant=None):
    sys.path[:0] = [str(ROOT / "src"), str(ROOT / TOOLS)]
    from VerifySdkCircleEndRegistration import OutputGuard
    from convert import open_document, write_document
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.registry import AdapterNotFoundError
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.api.ApiContext import GetRegistry
    from interchange.serialization.Deserialize import FromData

    raw = request["prior_projected_request"]
    assert set(raw) == {"document", "native_path", "creation_epoch"}
    document = external_anchor(FromData(raw["document"]), variant)
    document.assert_valid()
    warm()
    writer = GetRegistry().GetWriter(FORMAT)
    emitter = import_module("convert.adapters.solidworks.Core.Writing.EmitNativeMut")
    emitter.ReadTime = lambda: raw["creation_epoch"]
    registry_path = scratch / "Published" / "SignedBox.SLDPRT"
    direct_path = scratch / "Direct" / registry_path.name
    direct_path.parent.mkdir()
    guard = OutputGuard(scratch, registry_path.name)
    sys.addaudithook(guard.audit)
    policy = {"require_native_transfers": True}
    custody = {**policy, "final_destination": raw["native_path"]}
    if variant is not None:
        initial = b"previous bytes"
        staged = BytesIO(initial)
        with guard.active("memory"):
            assert not writer.supports(document, registry_path)
            for target, values in ((registry_path, policy), (staged, custody)):
                try:
                    write_document(document, target, destination_format=FORMAT, allow_carrier=False, values=values)
                except (ValueError, TypeError, AdapterNotFoundError):
                    continue
                raise ValueError("unqualified anchor was published")
        assert not registry_path.parent.exists() and staged.getvalue() == initial and staged.tell() == 0
        return {"refused": variant, "runtime_external_access_attempts": len(guard.denied)}

    with guard.active("memory"):
        assert writer.supports(document, registry_path)
        old_direct, old_public = BytesIO(), BytesIO()
        first = writer.write(document, old_direct, WriteOptions(values=custody))
        second = write_document(document, old_public, destination_format=FORMAT, allow_carrier=False, values=custody)
        exact = old_public.getvalue()
        assert old_direct.getvalue() == exact and digest(exact) == request["candidate_sha256"]
        check_reply(first, exact, None, document, False)
        check_reply(second, exact, None, document, True)
        streams = SldprtArchive.from_bytes(exact).streams
        assert {name: {"bytes": len(value), "sha256": digest(value)} for name, value in streams.items()} == request["streams"]
        fresh = BytesIO()
        fresh_options = {**policy, "final_destination": str(registry_path)}
        third = write_document(document, fresh, destination_format=FORMAT, allow_carrier=False, values=fresh_options)
        check_reply(third, fresh.getvalue(), None, document, True)
    with guard.active("path"):
        fourth = write_document(document, registry_path, allow_carrier=False, values=policy)
        fifth = writer.write(document, direct_path, WriteOptions(values=fresh_options))
    assert registry_path.read_bytes() == direct_path.read_bytes() == fresh.getvalue()
    assert tuple(registry_path.parent.iterdir()) == (registry_path,)
    check_reply(fourth, fresh.getvalue(), registry_path, document, True)
    check_reply(fifth, fresh.getvalue(), direct_path, document, False)
    opened = open_document(exact, source_format=FORMAT, strict=True)
    assert len(opened.bodies) == 1 and opened.bodies[0].name == document.bodies[0].name
    assert opened.brep is not None and (len(opened.brep.vertices), len(opened.brep.edges), len(opened.brep.faces)) == (8, 12, 6)
    assert sorted((value.name, value.value.value) for value in opened.parameters) == sorted(
        (value.name, value.value.value) for value in document.parameters)
    assert sum(rule.kind == "coincident" and rule.driving and not rule.suppressed
               for rule in opened.sketches[0].constraints) == 1
    return {"native_candidate_sha256": digest(exact), "exact_streams": len(streams), "guarded_public_routes": 5,
            "fresh_locator_sha256": digest(fresh.getvalue()), "runtime_external_access_attempts": len(guard.denied),
            "body_topology": [8, 12, 6], "live_parameters": len(opened.parameters), "active_origin_coincidence": True}


def compare(packet, pin, prior, scratch, receipt):
    assert os.name == "nt" and not scratch.exists()
    manifest = json.loads(payload(packet / "Freeze.json", pin))
    assert manifest["schema"] == SCHEMA and digest(HERE.read_bytes()) == manifest["method_sha256"]
    job = json.loads(payload(prior / "Job.json", PRIOR_JOB))
    result = json.loads(payload(prior / "Result.json", PRIOR_RESULT))
    assert result["passed"] and result["controls_healthy"] and result["distinct_processes"] == 6
    assert result["heldout_candidates_passed"] == len(SLOTS) and result["job_sha256"] == PRIOR_JOB
    sources = Path(r"C:\KitAttachedTopBoxSources02")
    scratch.mkdir()
    projector, code = scratch / "Projector", scratch / "Code"
    unpack(payload(prior / "Projector.zip", job["inputs"]["Projector.zip"]), projector)
    unpack(payload(packet / "Code.zip", manifest["archive_sha256"]), code)
    script = code / ENTRY
    payload(script, manifest["method_sha256"])
    outcomes = {}
    for slot in SLOTS:
        row = result["cases"][slot]
        source = sources / slot / "Native/Original.SLDPRT"
        known = row["original_source_sha256"]
        locator = Path(job["target"]) / slot / "SignedBox.SLDPRT"
        payload(source, known)
        projected = run((sys.executable, "-B", str(projector / PROJECTOR),
                         str(source), known, "--native-path", str(locator), "--creation-epoch", str(job["creation_epoch"])),
                        check=True, capture_output=True, timeout=120)
        assert not projected.stderr and digest(projected.stdout) == row["build"]["neutral_sha256"]
        request = json_bytes({"prior_projected_request": json.loads(projected.stdout),
                              "candidate_sha256": row["build"]["sha256"], "streams": row["build"]["streams"]})
        for variant in (None, *NEGATIVES):
            label = variant or "qualified"
            target = scratch / slot / label
            target.mkdir(parents=True)
            command = (sys.executable, "-I", "-B", str(script), "worker", str(target))
            if variant is not None:
                command += ("--negative", variant)
            probe = run(command, input=request, check=True, capture_output=True, timeout=120)
            assert not probe.stderr
            outcomes[slot + "/" + label] = json.loads(probe.stdout)
        payload(source, known)
    info = {"schema": SCHEMA, "passed": True, "source_commit": manifest["source_commit"],
            "source_tree": manifest["source_tree"], "frozen_code_sha256": manifest["archive_sha256"],
            "prior_native_result_sha256": PRIOR_RESULT, "prior_native_job_sha256": PRIOR_JOB,
            "measurements": outcomes, "heldout_candidate_matches": len(SLOTS), "new_native_oracle_launches": 0,
            "guarded_workers": len(outcomes), "writer_external_reads": 0, "new_benchmark_conversions": 0}
    return {"receipt_sha256": publish(receipt, json_bytes(info)), "heldout_candidate_matches": len(SLOTS)}


def freeze(directory):
    def git(*args):
        return run(("git", "-C", str(ROOT), *args), check=True, capture_output=True).stdout

    git("merge-base", "--is-ancestor", LOCK_REVISION, "HEAD")
    commit = git("rev-parse", "HEAD").decode().strip()
    src = git("rev-parse", "HEAD:src").decode().strip()
    code = git("show", "HEAD:" + ENTRY)
    assert code == HERE.read_bytes() and not directory.is_relative_to(ROOT)
    buffer = BytesIO(git("archive", "--format=zip", "HEAD", "src"))
    with ZipFile(buffer, "a") as archive:
        for name in (ENTRY, TOOLS + "VerifySdkCircleEndRegistration.py"):
            archive.writestr(name, git("show", "HEAD:" + name))
    directory.mkdir()
    publish(directory / HERE.name, code)
    archived = publish(directory / "Code.zip", buffer.getvalue())
    manifest = {"schema": SCHEMA, "source_commit": commit, "source_tree": src,
                "archive_sha256": archived, "method_sha256": digest(code)}
    return {"freeze_sha256": publish(directory / "Freeze.json", json_bytes(manifest)), **manifest}


if __name__ == "__main__":
    parser = ArgumentParser()
    modes = parser.add_subparsers(dest="mode", required=True)
    host = modes.add_parser("freeze")
    host.add_argument("directory", type=Path)
    guest = modes.add_parser("compare")
    for key in ("packet", "prior", "scratch", "receipt"):
        guest.add_argument(key, type=Path)
    guest.add_argument("--pin", required=True)
    child = modes.add_parser("worker")
    child.add_argument("scratch", type=Path)
    child.add_argument("--negative", choices=NEGATIVES)
    args = parser.parse_args()
    if args.mode == "freeze":
        value = freeze(args.directory)
    elif args.mode == "compare":
        value = compare(args.packet, args.pin, args.prior, args.scratch, args.receipt)
    else:
        value = worker(json.load(sys.stdin), args.scratch, args.negative)
    print(json.dumps(value, sort_keys=True, allow_nan=False))
