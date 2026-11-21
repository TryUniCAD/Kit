from math import isclose, radians
from pathlib import Path, PureWindowsPath

from ProveTwoDirectionRevolves import data, locked, need, process_identity


SHARE = PureWindowsPath(r"\\Mac\Home\Documents\UniCAD\Oracle121Takeover")
PRIOR = SHARE / "SquareComparisonHeldout01"
PRIVATE = PureWindowsPath(r"C:\KitSdkCandidates\SquareComparisonHeldout01")
SPEC = SHARE / "RevolveEqualHeldout01/Tool/Spec.json"
NATIVE = "re/solidworks/measurements/2026/SdkSquareRevolveHeldoutNative01.json"
PRELOCK = "re/solidworks/measurements/2026/RevolveEqualLengthSourceLock01.json"
NATIVE_SHA = "ef201f8e33168e74ae776e7e6b7efa52c9b5acb80f0d4910e565ea6ead1905be"
LOCK_SHA = "f083f56d7dad630ae2fbebda1c983ce06c8e5c935ace81317dc0f050b561cd53"
OLD_FREEZE = "b686987950c60a60304c5f122a8a2fe0c1025d2e0c9e6139ebce29854e758ba6"
GENERATION_SHA = "db79980e0fb470856651af82cfbe9f87f7b9fe938cf1c0c41d25661bf0eaeeb3"
LOCK_REV = "c9d64090b37b2fa56971662f926441aa9bb2be1f"
WRITER = "bc49a5acff6c3a5488b47623f6e2353f7cfad2be"
WRITER_TREE = "d69a52436090865d5d442acb090912fd3b4a7d88"
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
CASES = {"H-Square-01": "midplane", "H-Square-02": "two"}


def angle_matches(first, second):
    return isclose(first, second, rel_tol=1e-13, abs_tol=1e-14)


def edited_case(case):
    return dict(case, angle_deg=case["edit_angle_deg"], second_deg=case["edit_second_deg"])


def controls(private, native, lock):
    identities = []
    for role in ("before", "after"):
        row = native["controls"][role]
        control = data(private / (role + ".json"), row["sha256"])
        need(row["passed"] and control["sha256"] == lock["control_sha256"]
             and control["opened"] and control["open_errors"] == control["open_warnings"] == 0
             and control["rebuilt"] and control["whats_wrong"] == 0 and control["bodies"] > 0
             and control["mass"]["volume"] > 0 and not control.get("exception")
             and not control["dialogs"] and not control["controller_diagnostics"] and control["features"]
             and all(item["error"] == 0 and not item["warning"] for item in control["features"]),
             "both measured exact-build controls must be healthy")
        identities.append(process_identity(control))
    return identities


def equal_operands(state):
    rows = state["relation_operands"]
    pair, = (indices for code, indices in rows if code == 14)
    unary = sorted((code, indices) for code, indices in rows if code != 14)
    need(len(rows) == state["profile_relations"] == 5
         and sorted(indices[0] for _, indices in unary if len(indices) == 1) == list(range(4))
         and all(code in (4, 5) for code, _ in unary)
         and len(pair) == 2 and all(type(i) is int and 0 <= i < 4 for i in pair)
         and (pair[0] - pair[1]) % 4 in (1, 3), "actual unary and ordered square relation owners")
    return pair


def matching_state(first, second):
    compare = ("complete_tree", "body_names", "parents", "profile_relations", "relation_operands", "api_mode", "reverse")
    need(all(first[key] == second[key] for key in compare), "complete native tree and owner parity")
    a, b = first["mass"], second["mass"]
    need(all(format(a[key], ".6g") == format(b[key], ".6g") for key in ("volume", "area", "mass"))
         and all((abs(x) <= 1e-12 and abs(y) <= 1e-12) or format(x, ".6g") == format(y, ".6g")
                 for x, y in zip(a["com"], b["com"], strict=True)), "paired six-significant native mass")


def cycle(folder, pins, case):
    need(len(pins) == 2, "completed native edit and fresh reopen")
    first = data(folder / "Initial.json", pins[0])
    final = data(folder / "FreshReopen.json", pins[1])
    edited = edited_case(case)
    for row, phase, job in ((first, "reopen", case), (final, "edited-reopen", edited)):
        need(row["job"] == {"case": job, "phase": phase} and row["passed"] and row["source_immutable"]
             and row["inspection_completed"] and row["open_status"] == {"opened": True, "errors": 0, "warnings": 0}
             and row["before_explicit_rebuild"]["bodies"] == 1 and not row["dialogs"]
             and not row["controller_diagnostics"] and not row["first_failure"], "clean native edit and reopen observations")
    require_two = case["mode"] == "two"
    keys = ("angle_deg", "second_deg") if require_two else ("angle_deg",)
    expected_edits = [(f"D{index}", radians(case[key]), radians(edited[key])) for index, key in enumerate(keys, 1)]
    edit = first["edit"]
    saved = first["edited_derivative"]
    need(edit["passed"] and saved["save_status"] == [True, 0, 0] and len(edit["dimensions"]) == len(expected_edits),
         "actual named edit and clean native save")
    for row, (name, before, after) in zip(edit["dimensions"], expected_edits, strict=True):
        need(row["name"].split("@")[0] == name and row["setter_status"] == 0
             and angle_matches(row["before_radians"], before) and angle_matches(row["after_radians"], after), "live angle setter values")
    stages = {"reopened": (first["reopened"], case), "edited": (first["edited"], edited),
              "edited_fresh_reopen": (final["reopened"], edited)}
    if require_two:
        stages["after-d1"] = (first["after-d1"], dict(case, angle_deg=edited["angle_deg"]))
    for state, wanted in stages.values():
        need(equal_operands(state) == case["equal_edges"] and state["bodies"] == 1
             and len(state["complete_tree"]) == 25 and state["reverse"] == case["reverse"]
             and all(row["error"] == 0 and not row["warning"] for row in state["complete_tree"])
             and all(angle_matches(state["angles_radians"][index], radians(wanted[key]))
                     for index, key in enumerate(keys)), "actual five relations and independent drivers through native lifecycle")
    return {key: row for key, (row, _) in stages.items()}, saved["sha256"], [process_identity(row) for row in (first, final)]


def authorized_inputs(code):
    old = data(Path(PRIOR) / "Freeze.json", OLD_FREEZE)
    receipt = data(Path(PRIOR) / "NativeReceipt.json", NATIVE_SHA)
    lock = data(code / PRELOCK, LOCK_SHA)
    bound = old["writer_revision"] == receipt["writer_revision"] == WRITER
    need(bound and old["writer_source_tree"] == receipt["writer_source_tree"] == WRITER_TREE
         and receipt == data(code / NATIVE, NATIVE_SHA) and old["schema"] == receipt["schema"] == "kit.sw2026.square-revolve-comparison.v1"
         and old["split"] == receipt["split"] == lock["split"] == "heldout" and old["lock_sha256"] == LOCK_SHA
         and receipt["source_lock_sha256"] == LOCK_SHA and receipt["freeze_sha256"] == OLD_FREEZE
         and old["private"] == str(PRIVATE) and old["packet"] == str(PRIOR) and old["fixture"] == "RevolveEqualHeldout01"
         and old["method_revision"] == receipt["method_revision"] and old["sealed_inputs_opened_while_freezing"] == 0
         and receipt["oracle_sha256"] == lock["oracle_sha256"] == ORACLE and receipt["application_idle"]
         and receipt["passed"] and receipt["distinct_processes"] == 10 and receipt["heldout_writer_cases_qualified"] == 2
         and receipt["writer_external_access_attempts"] == 0 and lock["passed"] and lock["writer_output_count"] == 0
         and lock["distinct_processes"] == 8, "previous exact frozen writer and qualifying pre-writer source lock")
    spec = data(Path(SPEC), lock["spec_sha256"])
    need(spec["split"] == "heldout", "authorized neutral design spec")
    designs = {case["name"]: case for case in spec["cases"]}
    originals = {row["name"]: row for row in lock["sources"]}
    need(set(designs) == set(originals) == set(receipt["cases"]) == set(CASES), "only the measured square pair")
    private = Path(PRIVATE)
    need(receipt["generation_sha256"] == GENERATION_SHA, "exact generation receipt owner")
    generation = data(private / "Generation.json", GENERATION_SHA)
    process_ids = controls(private, receipt, lock)
    authorized = []
    for name, mode in CASES.items():
        slot, ref, built = receipt["cases"][name], originals[name], generation[name]
        need(slot["passed"] and ref["passed"] and ref["mode"] == designs[name]["mode"] == mode
             and not ref["reused_authored_phase"] and slot["source_sha256"] == ref["native_sha256"] == built["source_sha256"]
             and slot["candidate_sha256"] == built["candidate_sha256"] and slot["exact_streams"] == 10
             and len(built["candidate_streams"]) == 10 and built["path_and_stream_equal"]
             and built["runtime_external_access_attempts"] == 0 and built["native_relation_code"] == 14
             and built["same_ordered_contour_operands"] and built["strict_source_and_candidate_read"], "actual measured model provenance")
        phase = data(private / name / "Initial.json", slot["candidate_phases"][0])
        case = designs[name] | {"equal_edges": equal_operands(phase["reopened"])}
        source, _, ids = cycle(private / (name + "-source"), slot["source_phases"], case)
        generated, edited_sha, generated_ids = cycle(private / name, slot["candidate_phases"], case)
        need(set(source) == set(generated) == set(slot["comparisons"]), "complete prior native comparison")
        for key, counts in slot["comparisons"].items():
            need(counts == {"tree_rows": 25, "mass_checks": 6, "relation_count": 5}, "measured comparison count")
            matching_state(source[key], generated[key])
        process_ids += ids + generated_ids
        candidate = private / "Generated" / (name + ".SLDPRT")
        edited = private / name / (name + "-edited.SLDPRT")
        locked(candidate, slot["candidate_sha256"])
        locked(edited, edited_sha)
        authorized.append((case, int(old["frozen_at"]), candidate, slot["candidate_sha256"], edited, edited_sha, generated))
    need(len(set(process_ids)) == len(process_ids) == 10
         and all(process_ids[0] < stamp < process_ids[1] for stamp in process_ids[2:]), "native phases inside both healthy controls")
    return authorized
