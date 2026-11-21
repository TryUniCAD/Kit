from argparse import ArgumentParser
from base64 import b64decode
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path, PureWindowsPath
from struct import pack
from subprocess import check_output, run
import json
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[5]
BASE = "a155553908326ac89215735c1a7698f6481ed103"
LOCK_REVISION = "642b20cc65d14262ecc1e78e478af5ab48ca59b0"
LOCK = "re/solidworks/measurements/2026/RevolveCutHeldoutSourceLock01.json"
KEYWORDS = "src/convert/adapters/solidworks/Archive/Construction/Metadata/CheckRevKeys.py"
TOOL_ROOT = ROOT / "re/tooling/sw2026"
LOCAL_READERS = {
    "BuildStockCutSelector.py", "StockCutFixture.py", "StockCutGeometry.py", "StockCutPlan.py",
    "RunStockCutSelector.py", "FreezeStockCutSelector.py",
}
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(ROOT / "src"))

from RunStockCutSelector import (CONTROL_SHA, LOCK_SHA, ORACLE_SHA, POLICIES, SCHEMA, TOOLS,
                                 checked, digest, encode, publish, require, verify)
from convert.adapters.solidworks.Container.Container import SldprtArchive


def generate(locator, policy):
    proc = run((sys.executable, "-I", "-B", str(HERE.with_name("BuildStockCutSelector.py")), "--worker"),
               input=encode({"locator": locator, "policy": policy}), capture_output=True, timeout=90)
    require(proc.returncode == 0 and not proc.stderr, proc.stderr.decode())
    proof = json.loads(proc.stdout)
    raw = b64decode(proof.pop("data"), validate=True)
    require(len(raw) == proof["bytes"] and digest(raw) == proof["sha256"] and proof["zero_runtime_reads"],
            "worker response lost generated data or purity evidence")
    return raw, proof


def verify_contrast(first, second):
    a, x = first
    b, y = second
    require(x["case"] == y["case"] and a != b
            and x["config_counter"] == y["config_counter"] and x["resolved_counter"] == y["resolved_counter"],
            "native comparison requires a single model and archive link")
    affected = {key for key, value in x["streams"].items() if value != y["streams"].get(key)}
    key = x["resolved_key"]
    require(set(x["streams"]) == set(y["streams"]) and affected == {key} and key == y["resolved_key"],
            "unexpected additional stream changes across the selector arms")
    left, right = (SldprtArchive.from_bytes(value).require(key) for value in (a, b))
    positions = tuple(index for index, (l, r) in enumerate(zip(left, right, strict=True)) if l != r)
    require(len(positions) == 4 and positions == tuple(range(positions[0], positions[0] + 4))
            and left[positions[0]:positions[-1] + 1] == pack("<i", x["selector"]["producer_id"])
            and right[positions[0]:positions[-1] + 1] == pack("<i", -1)
            and y["selector"] == (x["selector"] | {"f108": -1}),
            "generated native comparison differs beyond the actual modeled f108")
    return {"only_stream": key, "typed_field": "cut.f548[0].f108", "changed_wire_bytes": 4,
            "equal_other_streams": len(x["streams"]) - 1, "same_logical_input": True}


def native_tools():
    for name in TOOLS:
        path = HERE.with_name(name) if name == "RunStockCutSelector.py" else TOOL_ROOT / name
        yield name, path.read_bytes()


def freeze(output, guest_packet, guest_work, control):
    require(output.is_absolute() and not output.exists() and not output.is_relative_to(ROOT)
            and guest_packet.is_absolute() and guest_packet.name == output.name
            and guest_work.drive.casefold() == "c:" and guest_work.is_absolute() and guest_work.name == "Work",
            "freeze requires fresh external paths and an exact guest-local locator")
    for revision in (BASE, LOCK_REVISION):
        check_output(("git", "merge-base", "--is-ancestor", revision, "HEAD"), cwd=ROOT)
    changes = check_output(("git", "diff", "--name-only", BASE, "--", "src"), cwd=ROOT, text=True).splitlines()
    require(changes == [KEYWORDS], "production closure contains unrelated changes")
    baseline_tree = check_output(("git", "rev-parse", BASE + ":src"), cwd=ROOT, text=True).strip()
    public_lock = checked(ROOT / LOCK, LOCK_SHA)
    known_control = checked(control, CONTROL_SHA)
    locator = str(guest_work / "RevolveCutSelector.SLDPRT")
    with ThreadPoolExecutor(max_workers=4) as pool:
        variants = list(pool.map(lambda label: generate(locator, label), (*POLICIES, *POLICIES)))
    for index in range(len(POLICIES)):
        require(variants[index] == variants[index + len(POLICIES)], "isolated repeated construction diverged")
    contrast = verify_contrast(*variants[:2])
    artifacts = {"SourceLock.json": public_lock, "Control/RevolveFull.SLDPRT": known_control,
                 **{f"Tools/{name}": raw for name, raw in native_tools()}}
    arms = {}
    for label, (raw, report) in zip(POLICIES, variants[:2], strict=True):
        artifacts[f"Candidates/{label}.SLDPRT"] = raw
        arms[label] = {key: value for key, value in report.items() if key != "case"}
    paths = {ROOT / KEYWORDS, TOOL_ROOT / "AuthorRevolveFamilies.py", TOOL_ROOT / "RevolveFamilyModel.py",
             *(HERE.with_name(name) for name in LOCAL_READERS),
             *(TOOL_ROOT / "revolve" / relative for relative in (
                 "PrincipalWriter/BuildPrincipalRevolves.py", "EndModes/AuditRevEndOwners.py",
                 "EndModes/ProveTwoDirectionRevolves.py", "Preparation/MakeRevolveRequest01.py",
                 "Preparation/ReadRevolveInput01.py",
             ))}
    manifest = {"schema": SCHEMA, "oracle_sha256": ORACLE_SHA, "writer_parent": BASE,
                "writer_parent_source_tree": baseline_tree, "source_lock_commit": LOCK_REVISION,
                "source_lock_sha256": LOCK_SHA, "guest_packet": str(guest_packet), "guest_work": str(guest_work),
                "encoded_locator": locator, "files": {name: digest(raw) for name, raw in artifacts.items()},
                "case": variants[0][1]["case"], "arms": arms, "contrast": contrast,
                "generation_tools": {path.relative_to(ROOT).as_posix(): digest(path.read_bytes()) for path in sorted(paths)},
                "guarded_generation_workers": len(variants), "runtime_input_reads": 0, "heldout_inputs_read": 0}
    output.mkdir()
    for name, raw in artifacts.items():
        path = output / name
        path.parent.mkdir(exist_ok=True)
        publish(path, raw)
    manifest_path = output / "Trial.json"
    manifest_sha = publish(manifest_path, encode(manifest))
    verify(manifest_path, manifest_sha)
    print(json.dumps({"manifest_sha256": manifest_sha, "paths": str(output), "changed_wire_bytes": positions_count(contrast),
                      "candidate_sha256": {label: arms[label]["sha256"] for label in POLICIES}}))


def positions_count(contrast):
    return contrast["changed_wire_bytes"]


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--guest-packet", type=PureWindowsPath, required=True)
    parser.add_argument("--guest-work", type=PureWindowsPath, required=True)
    parser.add_argument("--control", type=Path, required=True)
    args = parser.parse_args()
    freeze(args.output, args.guest_packet, args.guest_work, args.control)
