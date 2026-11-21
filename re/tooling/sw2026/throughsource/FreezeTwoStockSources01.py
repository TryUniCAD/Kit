from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
from secrets import randbelow
from time import time
import json
import os
import sys

HERE = Path(__file__).resolve()
PACKET = "TwoStockWriterHoldout01"
SCHEMA = "kit.sw2026.two-stock-writer-source-lock.v1"
STOCK_PROBE = "ProbeThroughMultiStock01.py"
SCOPE_PROBE = "ProbeThroughAutoScope01.py"
TOOL_PINS = {
    STOCK_PROBE: "b892caa8c228c816bb11cf81a04e2fefea8c9159ed952873b895798f64dabe4e",
    SCOPE_PROBE: "9d9065ea04a275b77e24371e74c7f98ebbfaa9fa2bc80bf774dd8e908a663f83",
}
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
BUILD = "34.5.2.0604"
PHASES = ("before", "a-author", "a-reopen", "b-author", "b-reopen", "after", "seal")


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(raw):
    return sha256(raw).hexdigest()


def wire(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def read_owned(path):
    require(path.is_file() and not path.is_symlink(), "a required file is missing or redirected")
    return path.read_bytes()


def write_new(path, value):
    raw = wire(value)
    with path.open("xb") as f:
        f.write(raw)
    return digest(raw)


def random_in(lo, hi):
    return lo + randbelow(hi - lo + 1)


def new_design(lower_centre, upper_centre):
    cx = random_in(lower_centre, upper_centre)
    radius = random_in(6500, 10500)
    moving_z = random_in(2300, 5150)
    a = (
        (cx - radius - random_in(1600, 4800), -radius - random_in(2200, 5300), 0),
        (cx + radius + random_in(1800, 4300), -random_in(2600, radius - 1400), random_in(11200, 17200)),
    )
    b = (
        (0, random_in(2450, radius - 1200), moving_z),
        (random_in(6850, 11250), radius + random_in(2000, 5000), moving_z + random_in(11000, 16500)),
    )
    return {
        "stationary_m": [[value / 1_000_000 for value in point] for point in a],
        "moving_initial_m": [[value / 1_000_000 for value in point] for point in b],
        "moving_edited_x_max_m": (cx + radius + random_in(2150, 5700)) / 1_000_000,
        "tool_center_m": [cx / 1_000_000, 0.0],
        "tool_radius_m": radius / 1_000_000,
    }


def prepare(root, freeze):
    root.mkdir(exist_ok=False)
    data = {"schema": SCHEMA, "public_freeze_sha256": freeze, "created_at": time(),
            "designs": {"a": new_design(23650, 29350), "b": new_design(33700, 40700)}}
    return {"passed": True, "private_plan_sha256": write_new(root / "PrivatePlan.json", data),
            "source_files_disclosed": 0, "native_processes_started": 0}


def load_packet(path, pin):
    raw = read_owned(path)
    require(digest(raw) == pin, "public freeze digest differs")
    data = json.loads(raw)
    require(data["schema"] == SCHEMA and data["packet"] == PACKET
            and data["oracle_build"] == BUILD and data["oracle_exe_sha256"] == ORACLE
            and data["phase_order"] == list(PHASES) and path.parent.name == PACKET
            and HERE == path.parent / HERE.name, "public freeze identity differs")
    for name, expected in data["tools"].items():
        require(digest(read_owned(path.parent / name)) == expected, "pinned author tool changed")
    require(all(data["tools"][k] == h for k, h in TOOL_PINS.items()), "wrong stock authors")
    return data


def load_private(root, freeze, private_pin):
    data = read_owned(root / "PrivatePlan.json")
    require(digest(data) == private_pin, "private plan digest differs")
    plan = json.loads(data)
    require(plan["schema"] == SCHEMA and plan["public_freeze_sha256"] == freeze, "private protocol differs")
    return plan


def inspect(root, slot, probe):
    work = root / slot
    author = probe.prior_phase(work, "AutoAuthor")
    reopen = probe.prior_phase(work, "AutoReopen")
    require(author["passed"] and reopen["passed"], "a native source failed a lifecycle")
    left, right = author["result"], reopen["result"]
    path = work / "AutoAuthor" / probe.PART
    raw = read_owned(path)
    key = left["saved_sha256"]
    require(digest(raw) == key == right["opened_sha256"] and len(raw) > 10000,
            "native saved source digest or size differs")
    require(probe.same_measured_model(left["after_save"], right["cold"])
            and probe.same_measured_model(left["after_edit"], right["after_edit"]),
            "native snapshots differ after fresh reopen")
    for event in (left["after_save"], right["cold"], left["after_edit"], right["after_edit"]):
        scope = event["cut_scope"]
        require(scope["feature_scope"] is True and scope["auto_select"] is False
                and event["moving_stock_cut"] is False, "native selected scope differs")
    return {"slot": slot, "sha256": key, "bytes": len(raw),
            "phase_sha256": [digest(read_owned(work / item / "Record.json")) for item in ("AutoAuthor", "AutoReopen")],
            "native_open_edit_reopen": True, "moving_stock_preserved": True}


def run(args):
    require(os.name == "nt", "source authoring requires the native Windows guest")
    packet = load_packet(args.freeze, args.pin)
    root = Path("C:/KitSdkCandidates") / PACKET
    require(root.resolve() == root and not root.is_symlink(), "private packet path is redirected")
    if args.phase == "prepare":
        return prepare(root, args.pin)
    private = load_private(root, args.pin, args.private_pin)
    sys.path.insert(0, str(HERE.parent))
    import ProbeThroughMultiStock01 as probe
    import ProbeThroughAutoScope01 as control

    trial_root = HERE.parent.with_name(probe.DISCLOSED)
    trial = control.disclosed(trial_root)
    sys.path.insert(0, str(trial_root / "Tools"))
    if args.phase in ("before", "after"):
        return control.measure(root, args.phase.capitalize(), trial_root, trial)
    if args.phase == "seal":
        controls = [root / phase / "Record.json" for phase in ("Before", "After")]
        require(all(json.loads(read_owned(path))["passed"] for path in controls), "native controls failed")
        slots = [inspect(root, slot, probe) for slot in ("a", "b")]
        require(slots[0]["sha256"] != slots[1]["sha256"], "independent source hashes coincide")
        result = {"schema": SCHEMA, "packet": PACKET, "passed": True,
                  "before_writer_revision": packet["before_writer_revision"], "public_freeze_sha256": args.pin,
                  "private_plan_sha256": args.private_pin, "oracle_exe_sha256": ORACLE, "oracle_build": BUILD,
                  "controls": [digest(read_owned(path)) for path in controls], "sources": slots,
                  "native_processes": 6, "source_files_disclosed": 0, "writer_evaluated": False}
        write_new(root / "SourceLock.json", result)
        return result
    require(probe.prior_phase(root, "Before")["passed"], "the leading native control failed")
    slot, action = args.phase.split("-")
    work = root / slot
    if action == "author":
        work.mkdir(exist_ok=False)
    else:
        require(probe.prior_phase(work, "AutoAuthor")["passed"], "native authoring did not pass")
    probe.DESIGN = private["designs"][slot]
    plan = {"schema": SCHEMA, "predictions": probe.predictions()}
    return probe.candidate(work, "Auto" + action.capitalize(), plan, args.pin)


if __name__ == "__main__":
    parser = ArgumentParser(description="Author and hash lock private native two-stock source models")
    parser.add_argument("phase", choices=("prepare", *PHASES))
    parser.add_argument("freeze", type=Path)
    parser.add_argument("pin")
    parser.add_argument("--private-pin")
    result = run(parser.parse_args())
    sys.stdout.buffer.write(wire(result))
    raise SystemExit(0 if result["passed"] else 1)
