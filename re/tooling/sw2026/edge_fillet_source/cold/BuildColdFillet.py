from argparse import ArgumentParser
from hashlib import sha256
from json import dumps, loads
from pathlib import Path, PureWindowsPath
from subprocess import check_output, run
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[5]
sys.path[:0] = [str(ROOT / "src"), str(ROOT), str(HERE.parent), str(HERE.parent.parent)]

from ColdFilletIntent import prepare_intent
from ComposeColdFillet import compose_fillet
from FilletModel import predict, require, validate_cases
from FilletPacket import job_bytes
from ProveFilletInputs import guard

from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput

INTENT_PIN = "d985611e397e943860b8b0ce4b3f9631e6c31f5355bdd784519a2b028a9a51cb"
EPOCH = 1795510277
GUEST_ROOT = PureWindowsPath(r"C:\KitEdgeFilletModelCold01")
NAMES = ("EdgeFilletAxial", "EdgeFilletTransverse")
RESEARCH = HERE.parent.parent.relative_to(ROOT)
STOCK_BUILDER = "tests/Convert/Solidworks/Research/Construction/Part/MakePlainDoc.py"
RADIUS_STREAMS = {"Contents/Config-0-ResolvedFeatures", "swXmlContents/KeyWords"}


def sha(data):
    return sha256(data).hexdigest()


def worker():
    case = loads(sys.stdin.buffer.read())
    require(type(case) is dict and "name" in case, "expected a neutral fillet object")
    require(case["name"] in NAMES, "unknown disclosed candidate name")
    locator = str(GUEST_ROOT / "Candidates" / (case["name"] + ".SLDPRT"))
    attempts = guard()
    data, streams, owners, graph_map, refusals = compose_fillet(prepare_intent(case, SelfFileInput(locator, EPOCH)))
    require(not attempts, "fillet compiler attempted external access")
    witness = {"encoded_locator": locator, "sha256": sha(data), "bytes": len(data), "owners": owners,
               "resolved_map": graph_map, "guarded_external_accesses": len(attempts), "refusals": refusals,
               "streams": {name: {"sha256": sha(raw), "bytes": len(raw)} for name, raw in streams.items()}}
    print(dumps({"bytes_hex": data.hex(), "witness": witness}, allow_nan=False))


def launch(case, *, expect_success=True):
    result = run((sys.executable, "-I", "-B", str(HERE), "--worker"),
                 input=job_bytes(case), capture_output=True, cwd=ROOT, timeout=60, check=False)
    if not expect_success:
        require(result.returncode != 0 and not result.stdout, "unsupported fillet emitted a file")
        return result.stderr.decode(errors="replace").strip().splitlines()[-1]
    require(result.returncode == 0 and not result.stderr, result.stderr.decode(errors="replace"))
    reply = loads(result.stdout)
    raw = bytes.fromhex(reply["bytes_hex"])
    require(sha(raw) == reply["witness"]["sha256"], "fillet candidate differs from guarded worker output")
    return raw, reply["witness"]


def write_new(path, raw):
    with path.open("xb") as stream:
        stream.write(raw)


def git(*args):
    return check_output(("git", *args), cwd=ROOT)


def stage(output, revision):
    require(git("rev-parse", "HEAD").decode().strip() == revision, "candidate needs the exact committed source revision")
    require(not git("status", "--porcelain", "--untracked-files=all", "--", "src", STOCK_BUILDER, str(RESEARCH)),
            "candidate needs clean pinned compiler and neutral tool paths")
    require(output.is_absolute() and output.resolve() == output and not output.is_relative_to(ROOT)
            and not output.exists(), "candidate packet needs a new exact path outside Kit")
    spec = git("show", f"{revision}:{RESEARCH.as_posix()}/DisclosedFilletInputs.json")
    require(sha(spec) == INTENT_PIN, "disclosed fillet job hash differs")
    cases = validate_cases(loads(spec))
    require(tuple(case["name"] for case in cases) == NAMES, "mismatched disclosed neutral fillet cases")
    results = {}
    for case in cases:
        intent = {name: value for name, value in case.items() if name != "edit_radius_mm"}
        first = launch(intent)
        require(first == launch(intent), "separate guarded compiler processes disagree")
        data, witness = first
        _, edited = launch(intent | {"radius_mm": case["edit_radius_mm"]})
        changed = {name for name, row in witness["streams"].items() if edited["streams"][name] != row}
        require(changed == RADIUS_STREAMS and edited["owners"] == (witness["owners"] | {
            "radius_m": case["edit_radius_mm"] / 1000.0
        }) and witness["resolved_map"] == edited["resolved_map"], "radius-only input changed an unrelated owner or stream")
        witness["radius_only"] = {"sha256": edited["sha256"], "changed_streams": sorted(changed),
                                  "radius_m": edited["owners"]["radius_m"],
                                  "guarded_external_accesses": edited["guarded_external_accesses"]}
        witness["analytic_initial"] = predict(case, case["radius_mm"] / 1000.0)
        witness["analytic_edited"] = predict(case, case["edit_radius_mm"] / 1000.0)
        results[case["name"]] = data, witness
    require(results[NAMES[0]][0] != results[NAMES[1]][0], "different neutral cases produced identical files")
    first_case = {name: value for name, value in cases[0].items() if name != "edit_radius_mm"}
    refusals = {
        "over_radius": launch(first_case | {"radius_mm": 200.0}, expect_success=False),
        "unmeasured_stock_fin": launch(first_case | {"corner": {"x": "min", "y": "min"}}, expect_success=False),
    }
    require("uniform radius exceeds" in refusals["over_radius"] and "measured carrier" in refusals["unmeasured_stock_fin"],
            "negative probes did not reach their intended preparation guards")
    tool_paths = (*sorted(HERE.parent.glob("*.py")), HERE.parent.parent / "FilletModel.py",
                  HERE.parent.parent / "FilletPacket.py", HERE.parent.parent / "ProveFilletInputs.py", ROOT / STOCK_BUILDER)
    tools = {path.relative_to(ROOT).as_posix(): sha(path.read_bytes()) for path in tool_paths}
    manifest = {"schema": "kit.sw2026.edge-fillet-model-cold.v1", "source_head": revision,
                "source_tree_at_head": git("rev-parse", f"{revision}:src").decode().strip(),
                "tools": tools, "neutral_intent_sha256": INTENT_PIN,
                "encoded_guest_root": str(GUEST_ROOT), "epoch": EPOCH, "fresh_guarded_processes": 8,
                "host_native_launches": 0, "native_accepted_candidates": 0, "refusals": refusals,
                "cases": {name: witness for name, (_, witness) in results.items()}}
    output.mkdir(parents=True, exist_ok=False)
    (output / "Candidates").mkdir()
    write_new(output / "Spec.json", spec)
    for name, (data, _) in results.items():
        write_new(output / "Candidates" / (name + ".SLDPRT"), data)
    raw_manifest = job_bytes(manifest)
    write_new(output / "Compile.json", raw_manifest)
    return {"manifest_sha256": sha(raw_manifest), "output": str(output), **manifest}


def main():
    parser = ArgumentParser()
    choices = parser.add_mutually_exclusive_group(required=True)
    choices.add_argument("--worker", action="store_true")
    choices.add_argument("--output", type=Path)
    parser.add_argument("--revision")
    args = parser.parse_args()
    if args.worker:
        worker()
    else:
        require(args.revision is not None, "provide the exact committed revision")
        print(dumps(stage(args.output, args.revision), sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
