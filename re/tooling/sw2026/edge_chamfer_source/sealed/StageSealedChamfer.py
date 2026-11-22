from argparse import ArgumentParser
from io import BytesIO
from math import dist
from pathlib import Path
from subprocess import check_output, run
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo
import json
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[5]
RESEARCH = "re/tooling/sw2026"
sys.path[:0] = [str(HERE.parent.parent), str(HERE.parent.parent.parent / "edge_fillet_source")]

from ChamferNeutralIntent import neutral_intent
from ChamferModel import predict
from ChamferPacket import TOOLS as SOURCE_TOOLS, write_new
from FilletPacket import BUILD, CONTROL, ORACLE, digest
from RunSealedChamfer import BOUNDARY_REV, DISCLOSED_FILE, DISCLOSED_REV, DISCLOSED_SHA, DRIVER_REV, ENTRY, EPOCH, FAMILY
from RunSealedChamfer import EVAL_PATH, LOCK_REV, PREWRITER_FILE, PREWRITER_SHA, PRIOR_FREEZE, PRIOR_RESULT
from RunSealedChamfer import SCHEMA, SOURCE_PATH, TOOLS, TRIAL, WRITER, WRITER_TREE
from RunSealedChamfer import compiler_bundle, generate, hash_bytes, require, verified

SHARED_CODE = {f"{RESEARCH}/{name}.py" for name in (
    "builders/EmptyPartition", "builders/Model", "builders/Views", "builders/Visual",
    "para/DownstreamIds", "para/Partition", "para/Schema", "para/Tracking", "para/concentric/CylinderFace",
    "para/prism/SdkPrismPartition", "para/rectangle/Allocate", "para/rectangle/AttributeChains",
    "para/rectangle/Attributes", "para/rectangle/Geometry", "para/rectangle/RectangleAttributes",
    "para/rectangle/RectanglePartition", "serial/Core", "serial/MapBridge",
)}
WRITER_CODE = {f"{FAMILY}/{name}.py" for name in (
    "BuildChamferBoundary", "ChamferEdgeOwners", "LinkChamferGraph", "MakeChamferDrivers",
    "ProveChamferDrivers", "ProveChamferEdgeOwners",
)}
INTEGRATION_CODE = {"tests/__init__.py", "tests/Convert/__init__.py", "tests/Convert/Solidworks/__init__.py",
                    "tests/Convert/Solidworks/Research/Construction/Part/MakePlainDoc.py",
                    "tests/Convert/Solidworks/Research/ConstructionGuard.py"}
STAGING_LEAVES = {f"{FAMILY}/sealed/{name}" for name in TOOLS | {HERE.name, Path(ENTRY).name}}


def git(*args):
    return check_output(("git", *args), cwd=ROOT)


def blob(revision, path):
    return git("show", f"{revision}:{path}")


def pinned_history():
    head = git("rev-parse", "HEAD").decode().strip()
    physical = git("rev-parse", BOUNDARY_REV).decode().strip()
    require(git("rev-parse", f"{WRITER}^{{tree}}").decode().strip() == WRITER_TREE
            and not git("diff", "--name-only", WRITER, head, "--", "src", *sorted(WRITER_CODE | SHARED_CODE | INTEGRATION_CODE))
            and not git("status", "--porcelain", "--", *sorted(STAGING_LEAVES)),
            "the host must freeze committed evaluator source and an untouched construction closure")
    for revision in (physical, DRIVER_REV, WRITER):
        git("merge-base", "--is-ancestor", LOCK_REV, revision)
    git("merge-base", "--is-ancestor", WRITER, head)
    require(len(set((LOCK_REV, physical, DRIVER_REV, WRITER))) == 4, "pre-writer proof requires distinct commits")
    return head, physical


def git_python_closure(head, writer=WRITER):
    exact = WRITER_CODE | SHARED_CODE | INTEGRATION_CODE
    trees = {}
    for raw in git("ls-tree", "-r", "-z", writer, "src", *sorted(exact)).split(b"\0"):
        if not raw:
            continue
        header, name = raw.decode().split("\t", 1)
        mode, kind, oid = header.split(" ")
        if name.endswith(".py"):
            require(mode == "100644" and kind == "blob", "compiler closure requires normal tracked Python files")
            trees[name] = oid
    require(exact <= trees.keys() and len(trees) > len(exact), "incomplete tracked constructor Python closure")
    ordered = sorted(trees)
    rows = run(("git", "cat-file", "--batch"), input="".join(trees[key] + "\n" for key in ordered).encode(),
               capture_output=True, cwd=ROOT, check=True)
    source = {}
    with BytesIO(rows.stdout) as stream:
        for name in ordered:
            oid, kind, length = stream.readline().decode().split()
            require((oid, kind) == (trees[name], "blob"), "git blob order or type differs")
            source[name] = stream.read(int(length))
            require(len(source[name]) == int(length) and stream.read(1) == b"\n", "git blob reading lost its boundary")
        require(not stream.read(1), "unexpected bytes after the tracked compiler source")
    source[ENTRY] = blob(head, ENTRY)
    return source


def zip_python(source):
    buffer = BytesIO()
    with ZipFile(buffer, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(source.items()):
            spec = ZipInfo(name, (2020, 1, 1, 0, 0, 0))
            spec.create_system = 3
            spec.external_attr = 0o100644 << 16
            archive.writestr(spec, data, compress_type=ZIP_DEFLATED, compresslevel=9)
    return buffer.getvalue()


def identity(contents):
    return {"bytes": len(contents), "sha256": hash_bytes(contents)}


def stage(output, control):
    output = output.resolve()
    require(output.name == TRIAL and not output.exists() and not output.is_relative_to(ROOT),
            "stage only at the unused managed disclosure root")
    earlier = output.parent / "GeneratedChamferHeldout01"
    previous_result = (earlier / "Public/Result.json").read_bytes()
    require(digest(earlier / "Packet/Freeze.json") == PRIOR_FREEZE and hash_bytes(previous_result) == PRIOR_RESULT,
            "the first freeze and result must remain immutable")
    head, physical = pinned_history()
    source = git_python_closure(head)
    assets = {f"Tool/{name}": blob(WRITER, f"{folder}/{name}") for folder, names in SOURCE_TOOLS.items() for name in names}
    assets.update({f"Tool/{name}": blob(head, f"{FAMILY}/sealed/{name}") for name in TOOLS})
    assets.update({"Tool/RunNativeChamferProbe.py": blob(WRITER, f"{FAMILY}/RunNativeChamferProbe.py"),
                   "Control.SLDPRT": control.read_bytes(), "Compiler.zip": zip_python(source),
                   "PrewriterLock.json": blob(LOCK_REV, PREWRITER_FILE),
                   "DisclosedReceipt.json": blob(DISCLOSED_REV, DISCLOSED_FILE),
                   "PriorEvaluation.json": previous_result})
    require([hash_bytes(assets[name]) for name in ("Control.SLDPRT", "PrewriterLock.json", "DisclosedReceipt.json")]
            == [CONTROL, PREWRITER_SHA, DISCLOSED_SHA], "public native evidence or healthy control seal differs")
    data = {"schema": SCHEMA, "evaluator_revision": head, "construction_revision": WRITER, "construction_tree": WRITER_TREE,
            "prewriter_lock_revision": LOCK_REV, "boundary_revision": physical, "driver_revision": DRIVER_REV,
            "disclosed_revision": DISCLOSED_REV, "oracle_build": BUILD, "oracle_sha256": ORACLE,
            "source_root": SOURCE_PATH, "evaluation_root": EVAL_PATH,
            "prior_freeze_sha256": PRIOR_FREEZE, "prior_result_sha256": PRIOR_RESULT,
            "complete_fresh_processes": 10, "epochs": [EPOCH, EPOCH + 1],
            "compiler_members": {name: identity(blob) for name, blob in source.items()},
            "files": {name: identity(blob) for name, blob in assets.items()}}
    packet = output / "Packet"
    packet.mkdir(parents=True, exist_ok=False)
    (output / "Public").mkdir()
    for name, contents in assets.items():
        path = packet / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as sink:
            sink.write(contents)
    write_new(packet / "Freeze.json", data)
    pin = digest(packet / "Freeze.json")
    verified(packet, pin)
    return pin


def smoke(packet, pin):
    sys.path.insert(0, str(HERE.parent.parent))
    from StageGeneratedChamfer import candidate_plan, composed_requests

    freeze, _ = verified(packet, pin)
    exact = json.loads((packet / "DisclosedReceipt.json").read_bytes())["generated_inputs"]
    counts, shifted = [], []
    with TemporaryDirectory(prefix="KitSealedChamferSmoke") as folder:
        root = Path(folder)
        compiler = compiler_bundle(packet, root / "Compiler", freeze["compiler_members"])
        for index, request in enumerate(composed_requests()):
            case, branch = candidate_plan(request, index)
            proof = generate(compiler, {"origin_mm": [0.0, 0.0], "request": request},
                             root / f"OriginalCompatibility{index}.SLDPRT", root / f"Parity{index}")
            require(proof["archive_sha256"] == exact[index], "frozen writer differs from its actual disclosed native input")
            counts.append(proof["archive_bytes"])
            offset = [-17.125, 5.75] if index == 0 else [58.375, -16.25]
            new_name = "ShiftedCompatibility" + ("A" if index == 0 else "B")
            moved = case | {"center_mm": offset, "name": new_name}
            locator = f"C:\\KitChamferIndependentSmoke\\{new_name}.SLDPRT"
            proof = generate(compiler, neutral_intent(moved, branch, locator, EPOCH + index),
                             root / f"{new_name}.SLDPRT", root / f"Shifted{index}")
            separate = proof["archive_sha256"] not in exact
            endpoints = zip(proof["selected_endpoints_m"], predict(moved)["source_edge"], strict=True)
            require(separate and proof["runtime_accesses"] == 0 and proof["driver_count"] == 2
                    and all(dist(actual, wanted) <= 1e-12 for actual, wanted in endpoints),
                    "generated shifted stock lost its separate shape or actual drivers")
            shifted.append(proof["archive_sha256"])
            try:
                neutral_intent(moved, [branch[0], "cot"], locator, EPOCH)
            except ValueError:
                pass
            else:
                raise ValueError("unsupported bevel relation reached neutral emission")
    return {"freeze_sha256": pin, "compiler_files": len(freeze["compiler_members"]), "disclosed_exact_sha256": exact,
            "disclosed_bytes": counts, "independent_shifted_sha256": shifted, "guarded_writer_processes": 8,
            "runtime_accesses": 0, "unsupported_cotangent_refusals": 2, "native_processes": 0}


def main():
    parser = ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--control", required=True, type=Path)
    args = parser.parse_args()
    pin = stage(args.output, args.control)
    print(json.dumps(smoke(args.output / "Packet", pin), sort_keys=True))


if __name__ == "__main__":
    main()
