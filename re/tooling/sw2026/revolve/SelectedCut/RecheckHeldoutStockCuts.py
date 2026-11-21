from argparse import ArgumentParser
from hashlib import sha256
import json
import os
from pathlib import Path, PureWindowsPath
import sys


PREFIX = PureWindowsPath(r"C:\KitSdkCandidates")
SELECTED = "re/tooling/sw2026/revolve/SelectedCut"
SCHEMA = "kit.sw2026.heldout-selected-revolve-read-recheck.v1"


def classify(error):
    text = str(error)
    for marker, branch in (
        ("selected revolve wrapper", "selected_stock_wrapper"),
        ("selected revolve cut face", "face_owner"),
        ("actual stock chooser", "chooser_owner"),
        ("actual two-body geometry", "solid_owner"),
        ("unexpected_runtime_reads", "runtime_access"),
    ):
        if marker in text:
            return branch
    return type(error).__name__


def evaluate(packet, freeze_pin, candidate_pin, native_pin):
    if os.name != "nt" or packet.name != "ScopedRevolveHeldoutEval03":
        raise ValueError("use the exact guest-local sealed evaluation")
    private = Path(PREFIX / packet.name)
    sys.path.insert(0, str(private / "Code" / SELECTED))
    from EvaluateHeldoutStockCuts import LOCK, LOCK_SHA, checked, encode, publish, require, verify
    from MatchHeldoutStockCuts import contrast, dispatch, native_receipt, originals, source_states
    from RunScopedRevolveNative import ORACLE_SHA, source_lock, validate_specs

    method, owned, source = verify(packet, freeze_pin)
    require(private == owned, "unexpected private evaluation location")
    area = owned / "CandidatePacket"
    candidate = json.loads(checked(area / "Packet.json", candidate_pin))
    terminal = json.loads(checked(area / "Inspection" / "Result.json", native_pin))
    require(terminal["packet_sha256"] == candidate_pin and candidate["freeze_sha256"] == freeze_pin
            and terminal["passed"] and terminal["controls_healthy"] and terminal["idle_after"]
            and terminal["distinct_processes"] == 6 and terminal["oracle_sha256"] == ORACLE_SHA
            and terminal["codec_revision"] == candidate["codec_revision"] == method["writer_revision"],
            "no exact native candidate outcome for this frozen writer")
    for role in ("before", "after"):
        row = terminal[role]
        raw = checked(area / "Inspection" / f"Control{role.title()}.json", row["sha256"])
        require(row["passed"] and json.loads(raw)["oracle_identity"]["sha256"] == ORACLE_SHA,
                "native control differs from the frozen oracle")
    custody = source_lock(checked(source / LOCK, LOCK_SHA))
    cases = validate_specs(json.loads(checked(area / "ModelSpecs.json", custody["spec_sha256"])))
    evidence = {}
    for case, locked in zip(cases, custody["sources"], strict=True):
        label = locked["case"]
        name = case["name"]
        trial = terminal["cases"][name]
        phase_root = area / "Inspection" / name
        initial, last = (native_receipt(phase_root / file, item["sha256"])
                         for file, item in zip(("Initial.json", "FreshReopen.json"), trial["phases"], strict=True))
        source_chain, parts = source_states(case, locked)
        candidate_chain = originals(initial, last)
        comparisons = [contrast(a, b) for a, b in zip(source_chain, candidate_chain, strict=True)]
        source_case = {"reopened": source_chain[0], "job": {"case": case}}
        edited_case = {"reopened": source_chain[2], "job": {"case": dict(case, angle_deg=case["edit_angle_deg"])}}
        states = (("locked_original", parts[0], source_case), ("locked_edit", parts[1], edited_case),
                  ("generated_edit", (phase_root / "Saved.SLDPRT", trial["saved_sha256"]), last))
        reads = {}
        for state, (file, pin), observed in states:
            try:
                read = dispatch(file, pin, observed=observed)
            except (OSError, TypeError, ValueError) as error:
                reads[state] = {"passed": False, "boundary": classify(error)}
            else:
                reads[state] = {"passed": True, "runtime_reads": read["unexpected_runtime_reads"],
                                "linked_streams": len(read["exact_streams"])}
        evidence[label] = {
            "native": {"passed": all(all(row.values()) for row in comparisons),
                       "checks": comparisons, "native_tree_rows": [
                           [len(a["features"]), len(b["features"])]
                           for a, b in zip(source_chain, candidate_chain, strict=True)]},
            "strict_reads": reads,
            "source_sha256": locked["native_sha256"],
            "candidate_sha256": trial["candidate_sha256"],
        }
    passed = all(row["native"]["passed"] and all(value["passed"] for value in row["strict_reads"].values())
                 for row in evidence.values())
    receipt = {
        "schema": SCHEMA, "observer_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "freeze_sha256": freeze_pin, "candidate_packet_sha256": candidate_pin, "native_result_sha256": native_pin,
        "locked_source_sha256": LOCK_SHA, "writer_revision": method["writer_revision"],
        "native_controls_healthy": True, "new_native_launches": 0,
        "original_native_files_read_by_generation": candidate["original_native_files_read_by_generation"],
        "passed": passed, "cases": evidence,
    }
    pin = publish(private / "ReadRecheck01.json", encode(receipt))
    return {"sha256": pin, "passed": passed,
            "native_parity_cases": sum(row["native"]["passed"] for row in evidence.values()),
            "strict_saved_reads": sum(value["passed"] for row in evidence.values() for value in row["strict_reads"].values())}


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--freeze-pin", required=True)
    parser.add_argument("--candidate-pin", required=True)
    parser.add_argument("--native-pin", required=True)
    args = parser.parse_args()
    try:
        status = evaluate(args.packet, args.freeze_pin, args.candidate_pin, args.native_pin)
    except Exception as error:
        print(json.dumps({"completed": False, "error_type": type(error).__name__}))
        raise SystemExit(1) from None
    print(json.dumps(status, sort_keys=True))
    raise SystemExit(int(not status["passed"]))
