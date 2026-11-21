from argparse import ArgumentParser
from base64 import b64decode
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path, PureWindowsPath
from subprocess import check_output, run
import json
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[5]
TOOLS_ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent))

from RunScopedRevolveNative import (
    CONTROL, CONTROL_SHA, MODEL, ORACLE_SHA, PREFIX, SCHEMA, TOOLS,
    checked, encode, path_for, publish, require, validate_specs, verify,
)
from RunStockCutSelector import digest


def git(*args):
    return check_output(("git", *args), cwd=ROOT)


def path_for_tool(name):
    local = HERE.with_name(name)
    return local if local.is_file() else TOOLS_ROOT / name


def make_candidate(case, workspace, epoch):
    script = HERE.with_name("BuildStockCutSelector.py")
    locator = str(workspace / path_for(case))
    request = {"locator": locator, "policy": "sentinel", "case": case, "epoch": epoch}
    process = run((sys.executable, "-I", "-B", str(script), "--worker"),
                  input=encode(request), capture_output=True, timeout=90)
    require(process.returncode == 0 and not process.stderr, process.stderr.decode())
    data = json.loads(process.stdout)
    raw = b64decode(data.pop("data"), validate=True)
    require(data.pop("case") == case and data["sha256"] == digest(raw)
            and data["bytes"] == len(raw) and data["zero_runtime_reads"],
            "construction output abandoned its model or process evidence")
    return raw, data


def freeze(output, packet, workspace, control, epoch):
    require(output.is_absolute() and not output.exists() and not output.is_relative_to(ROOT)
            and packet.is_absolute() and packet.name == output.name
            and workspace.is_absolute() and workspace.parent == PREFIX,
            "prepare a new external packet and an unused guest workspace")
    watched = ("src", "re/tooling/sw2026")
    require(not git("diff", "--name-only", "HEAD", "--", *watched)
            and not git("ls-files", "--others", "--exclude-standard", "--", *watched),
            "commit the exact construction and capture tools before freezing")
    source = HERE.with_name("StockCutPrincipalDisclosures01.json").read_bytes()
    cases = validate_specs(json.loads(source))
    require({(case["plane"], case["scope"]) for case in cases} == {("top", "inner"), ("right", "outer")},
            "disclosed packet must vary actual principal frame and selected stock")
    artifacts = {CONTROL: checked(control, CONTROL_SHA), MODEL: source,
                 **{f"Tools/{name}": path_for_tool(name).read_bytes() for name in TOOLS}}
    with ThreadPoolExecutor(max_workers=4) as workers:
        samples = list(workers.map(lambda item: make_candidate(item, workspace, epoch), (*cases, *cases)))
    proof = {}
    for i, case in enumerate(cases):
        require(samples[i] == samples[i + len(cases)], "fresh construction processes diverged")
        raw, item = samples[i]
        artifacts[f"Candidates/{path_for(case)}"] = raw
        proof[case["name"]] = item
    data = {
        "schema": SCHEMA,
        "oracle_sha256": ORACLE_SHA,
        "codec_revision": git("rev-parse", "HEAD").decode().strip(),
        "codec_src_tree": git("rev-parse", "HEAD:src").decode().strip(),
        "guest_packet": str(packet),
        "guest_workspace": str(workspace),
        "epoch": epoch,
        "generation_workers": len(samples),
        "runtime_reads": 0,
        "new_heldout_credit": 0,
        "construction": proof,
        "files": {name: digest(raw) for name, raw in artifacts.items()},
    }
    output.mkdir()
    for name, raw in artifacts.items():
        destination = output / name
        destination.parent.mkdir(exist_ok=True)
        publish(destination, raw)
    manifest = output / "Packet.json"
    pin = publish(manifest, encode(data))
    verify(manifest, pin)
    print(json.dumps({"packet_sha256": pin,
                      "candidates": {name: row["sha256"] for name, row in proof.items()}}))


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--guest-packet", type=PureWindowsPath, required=True)
    parser.add_argument("--guest-workspace", type=PureWindowsPath, required=True)
    parser.add_argument("--control", type=Path, required=True)
    parser.add_argument("--epoch", type=int, required=True)
    args = parser.parse_args()
    freeze(args.output, args.guest_packet, args.guest_workspace, args.control, args.epoch)
