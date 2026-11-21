import json
from pathlib import PureWindowsPath

from AuditThinArchive import CASES, ORACLE, SOURCE_LOCK, VERSION, checked_bytes, load_lock, phase, receipt
from AuditRevEndOwners import require

OTHER_LOCK = "7475170f6f524ba33fe826b54976f7d2793c9bd603851d1a31866220d26c6253"
OTHER_CASES = {"ThinTopOppositeControl": 1, "ThinRightCenterControl": 2}
BASELINES = {
    "front": (
        SOURCE_LOCK, CASES, 14,
        "33a91b5797f3e5c8374f962ff9803e7770b248b8e0150633f7ddd5e42e9285f0",
        "cdada047b9f9bd7be97b62383c07bcee06a527a69152af83d932801e2a556b5c",
    ),
    "principal": (
        OTHER_LOCK, OTHER_CASES, 8,
        "21228b9c95c2135a826bbbdb7d1c0abd37ff94de08d34fc6f59c934d64fe9a6a",
        "f0cae9a898ea4ed54a7e181b8631da6ff17569eca430558c4c77004b36d37127",
    ),
}


def load_baseline(capture, packet, terminal, group):
    lock_pin, modes, processes, build_pin, terminal_pin = BASELINES[group]
    if group == "front":
        lock, rows = load_lock(capture)
    else:
        lock = json.loads(checked_bytes(capture / "SourceLock.json", lock_pin))
        rows = {row["case"]: row for row in lock["sources"]}
    native = json.loads(checked_bytes(terminal, terminal_pin))
    build = json.loads(checked_bytes(packet / "BuildReceipt.json", build_pin))
    spec = json.loads(checked_bytes(packet / "ModelSpec.json", lock["spec_sha256"]))
    cases = {row["name"]: row for row in spec["cases"]}
    require(lock["split"] == spec["split"] == "discovery" and lock["family"] == spec["family"] == "thin"
            and lock["passed"] and not lock["heldout_writer_acceptance"] and not lock["writer_output_count"]
            and lock["fresh_processes"] == lock["distinct_processes"] == processes
            and lock["idle_after"] and lock["inputs_unchanged"] and lock["tools_unchanged"]
            and tuple(rows) == tuple(cases) == tuple(modes)
            and native["passed"] and native["build_receipt_sha256"] == build_pin
            and native["source_lock_sha256"] == lock_pin and native["inputs_unchanged"],
            "unexpected disclosed source or generated baseline inventory")
    require(all(row["oracle_sha256"] == ORACLE and row["oracle_build"] == VERSION for row in (native, lock)),
            "disclosed readback requires the pinned native build")
    for key in ("control-before", "control-after"):
        control = receipt(capture / (key + ".json"), lock[key]["sha256"])
        require(lock[key]["passed"] and native[key]["passed"] and control["sha256"] == lock["control_sha256"]
                and control["opened"] and control["rebuilt"]
                and control["open_errors"] == control["open_warnings"] == control["whats_wrong"] == 0,
                "disclosed readback lacks its healthy bracket controls")
    captured = {row["case"]: row for row in native["cases"]}
    require(tuple(captured) == tuple(build["rows"]) == tuple(modes)
            and all(build["rows"][name]["sha256"] == captured[name]["candidate_sha256"] for name in modes),
            "native lifecycle does not pin the same generated candidates")
    return lock, rows, cases, build, captured


def source_input(capture, row, mode, edited):
    name = row["case"]
    author, before, after = (phase(capture, name, info) for info in row["phases"])
    save = before["edited_derivative"]
    roles = ("angle", "wall1", "wall2") if mode == 3 else ("angle", "wall1")
    require(row["passed"] and author["native_sha256"] == row["native_sha256"]
            and save["save_status"] == [True, 0, 0] and before["edit"]["passed"]
            and tuple(edit["role"] for edit in before["edit"]["dimensions"]) == roles,
            "source and native edited derivative did not stay paired")
    source = after if edited else before
    state = source["reopened"]
    require(state["definition"]["wall_mode"] == mode and tuple(state["drivers"]) == roles,
            "unexpected native editable driver inventory")
    pin = save["sha256"] if edited else row["native_sha256"]
    size = save["bytes"] if edited else row["native_bytes"]
    suffix = "-edited" if edited else ""
    raw = checked_bytes(capture / name / (name + suffix + ".SLDPRT"), pin)
    require(len(raw) == size, "disclosed native part size differs")
    return raw, pin, state


def cold_input(packet, build, name, group):
    pin = build["rows"][name]["sha256"]
    filename = name + ".SLDPRT"
    raw = checked_bytes(packet / "Candidates" / filename, pin)
    root = build["logical_candidate_directory"] if group == "front" else r"C:\KitThinPlaneGenerated01\Candidates"
    epoch = build.get("epoch", build.get("common_epoch"))
    return raw, pin, str(PureWindowsPath(root, filename)), epoch
