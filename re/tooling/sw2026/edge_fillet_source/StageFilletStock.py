from argparse import ArgumentParser
from dataclasses import replace
from json import dumps, loads
from pathlib import Path
from subprocess import check_output, run
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
RESEARCH = HERE.parent.relative_to(ROOT).as_posix()
BUILDER = "tests/Convert/Solidworks/Research/Construction/Part/MakePlainDoc.py"
sys.path[:0] = [str(ROOT / "src"), str(ROOT), str(HERE.parent)]

from FilletModel import require, validate_cases
from FilletPacket import CONTROL, SHARED_TOOLS, job_bytes
from FilletStockPacket import (
    EPOCH, INTENT_SHA, NAMES, ORACLE_AUTHORITY, OWNED_TOOLS, SCHEMA,
    guest_root, load_job, pinned, sha, stock_target, write_new,
)


def stock_worker():
    from ProveFilletInputs import guard
    from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
    from convert.adapters.solidworks.Archive.Construction.Part.MakeBlindPart import MakeBlindByPlan
    from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectPlain import ProjectPlain
    from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
    from interchange.geometry.Models.GeometryCurves import LineGeometry
    from interchange.geometry.Models.VectorPlane import PlaneVector
    from tests.Convert.Solidworks.Research.Construction.Part.MakePlainDoc import MakePlainDoc

    request = loads(sys.stdin.buffer.read())
    require(set(request) == {"guest_root", "name", "center_mm", "size_mm"}, "expected neutral stock geometry only")
    locator = stock_target(guest_root(request["guest_root"]), request["name"])
    attempts = guard()
    plain = MakePlainDoc(request["name"], *request["size_mm"])
    (sketch,) = plain.sketches
    cx, cy = request["center_mm"]

    def translate(point):
        return PlaneVector(point.x + cx, point.y + cy)

    entities = tuple(replace(entity, geometry=LineGeometry(translate(entity.geometry.start), translate(entity.geometry.end)))
                     for entity in sketch.entities)
    document = replace(plain, sketches=(replace(sketch, entities=entities),),
                       configurations=(replace(plain.configurations[0], name="Default"),))
    plan = ProjectPlain(document)
    recipe = replace(MakePartRecipe(plan, EPOCH), OutputValue=SelfFileInput(locator, EPOCH))
    built = MakeBlindByPlan(document, recipe, plan)
    require(len(built.StreamsValue) == 10 and not attempts, "stock generation left the proved no-read ordinary part route")
    witness = {"encoded_locator": locator, "logical_streams": len(built.StreamsValue),
               "sha256": sha(built.BytesValue), "guarded_external_accesses": len(attempts)}
    print(dumps({"bytes_hex": built.BytesValue.hex(), "witness": witness}, allow_nan=False))


def git(*args):
    return check_output(("git", *args), cwd=ROOT)


def build_stock(case, root):
    request = {field: case[field] for field in ("name", "center_mm", "size_mm")}
    response = run((sys.executable, "-I", "-B", str(HERE), "--worker"), cwd=ROOT,
                   input=job_bytes(request | {"guest_root": str(root)}), capture_output=True, timeout=60, check=False)
    require(response.returncode == 0 and not response.stderr, response.stderr.decode(errors="replace"))
    result = loads(response.stdout)
    data = bytes.fromhex(result["bytes_hex"])
    require(sha(data) == result["witness"]["sha256"], "guarded stock worker output changed in transport")
    return data, result["witness"]


def stage(revision, control, output, guest):
    root = guest_root(guest)
    require(git("rev-parse", "HEAD").decode().strip() == revision, "operator pin differs from exact tool checkout")
    exact_paths = ("src", BUILDER, RESEARCH)
    require(not git("status", "--porcelain", "--untracked-files=all", "--", *exact_paths),
            "stock construction needs a clean pinned source and research closure")
    require(output.is_absolute() and output.resolve() == output and output.name == "Packet"
            and not output.is_relative_to(ROOT) and not output.exists(), "choose a fresh direct host Packet path outside Kit")
    spec = git("show", f"{revision}:{RESEARCH}/DisclosedFilletInputs.json")
    require(sha(spec) == INTENT_SHA, "disclosed stock intent changed")
    cases = validate_cases(loads(spec))
    require(tuple(case["name"] for case in cases) == NAMES, "unexpected disclosed stock cohort")
    files = {"Spec.json": spec}
    construction = {}
    for case in cases:
        name = case["name"]
        files[f"Stock/{name}.SLDPRT"], construction[name] = build_stock(case, root)
    require(len({row["sha256"] for row in construction.values()}) == len(cases), "distinct neutral stocks emitted the same bytes")
    files["Control.SLDPRT"] = pinned(control.absolute(), CONTROL)
    for folder, names in ((RESEARCH, OWNED_TOOLS), ("re/tooling/sw2026", SHARED_TOOLS)):
        for name in names:
            files[f"Tool/{name}"] = git("show", f"{revision}:{folder}/{name}")
    job = {"schema": SCHEMA, "written_at": EPOCH, "tool_revision": revision,
           "sdk_tree": git("rev-parse", revision + ":src").decode().strip(), "guest_root": str(root),
           "scope": "two disclosed model-only blind stocks", "fillet_writer_output_count": 0,
           "oracle": ORACLE_AUTHORITY, "construction": construction,
           "files": {name: {"sha256": sha(raw), "bytes": len(raw)} for name, raw in files.items()}}
    output.mkdir(parents=True, exist_ok=False)
    for name in ("Stock", "Tool"):
        (output / name).mkdir()
    for name, raw in files.items():
        write_new(output / name, raw)
    raw = job_bytes(job)
    path = output / "StockJob.json"
    write_new(path, raw)
    pin = sha(raw)
    load_job(path, pin)
    return {"stock_job_sha256": pin, "tool_revision": revision, "sdk_tree": job["sdk_tree"],
            "construction": construction, "host_native_launches": 0, "fillet_writer_output_count": 0}


def main():
    parser = ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--revision")
    parser.add_argument("--control", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--guest-root")
    args = parser.parse_args()
    if args.worker:
        stock_worker()
    else:
        require(all((args.revision, args.control, args.output, args.guest_root)), "provide the exact staging paths and revision")
        print(dumps(stage(args.revision, args.control, args.output, args.guest_root), sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
