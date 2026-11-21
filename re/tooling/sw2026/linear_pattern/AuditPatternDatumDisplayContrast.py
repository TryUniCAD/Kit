from argparse import ArgumentParser
from pathlib import Path
from struct import pack
import json
import sys

HERE = Path(__file__).resolve()
sys.path[:0] = [str(HERE.parent), str(HERE.parents[1])]

from AuditPatternDatumPlacement import replay
from AuditPatternEnvelope import Obj, need_node, node_name, vector
from MakePatternPrincipalDisplay import name_corner, PrincipalFrame
from PatternHingeGeometry import ORIGIN, principal_displays
from RunPatternDatumDisplayContrast import ARMS, BUILD, CONTROL, ORACLE, SCHEMA, TRIAL, checked, digest, require, verify
from PatternEnvelopePacket import encode
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectPlain import ProjectPlain
from interchange.serialization.Deserialize import FromData


TRIAL_PIN = "823829cf644ed55b08278bbfec785a99330e098bee119f8bcfd120b8428449dd"
RESULT_PIN = "041ba50b5f4508e1c4b9b5c92f82bc670b4c5079137ebc4dc7d31bf50272898f"


def control(out, row, side):
    native = json.loads(checked(out / ("Control-" + side + ".json"), row["record_sha256"]))
    identity = native["oracle_identity"]
    require(native["sha256"] == CONTROL and identity["file_version"] == BUILD and identity["sha256"] == ORACLE
            and native["opened"] and native["rebuilt"] and not native["dialogs"]
            and native["open_errors"] == native["open_warnings"] == native["whats_wrong"] == 0 and row["passed"],
            "native control did not bracket this exact model build")
    return identity["process_creation_filetime"]


def phase(out, entry, label, expected_tree):
    native = json.loads(checked(out / label / "Record.json", entry["record_sha256"]))
    state = native["result"]
    require(state == {name: row for name, row in entry.items() if name != "record_sha256"}
            and state["passed"] and native["passed"] and not native["dialogs"]
            and not native["first_failure"] and not native["cleanup_errors"]
            and state["open_counts"] == [0, 0] and not state["controller_diagnostics"]
            and state["identity"]["file_version"] == BUILD and state["identity"]["sha256"] == ORACLE,
            "native source phase did not remain clean")
    require(all(row["passed"] for row in native["checks"]) and len(native["checks"]) == (66 if label.endswith("-edit") else 44)
            and all([[r["name"], r["type"], r["parent"]] for r in snap["tree"]] == expected_tree
                    and snap["body_count"] == 1 and snap["dimension_driving"] and snap["whats_wrong"] == 0
                    for snap in state["states"].values()), "native scope or exact tree differs")
    displays = state["displays"]
    require(all(row["matches"] for rows in displays.values() for row in rows.values()), "native display comparison failed")
    return {"process": state["identity"]["process_creation_filetime"], "numeric_checks": len(native["checks"]),
            "displays": displays, "source_path": native["job"]["source"], "source_sha256": native["job"]["sha256"],
            "record_sha256": entry["record_sha256"], "saved": state.get("saved")}


def saved_presentation(path, pin, bounds):
    _, roots, streams = replay(checked(path, pin["sha256"], pin["bytes"]))
    displays = principal_displays(bounds)
    for axis, name in (("y", "Top Plane"), ("x", "Right Plane")):
        (node,) = [value for value in roots if isinstance(value, Obj) and value.cls == "moRefPlane_c" and node_name(value) == name]
        fields = need_node(node["f6f8"], "moDefaultRefPlnData_c")
        center, borders = displays[name]["display_root_m"], displays[name]["borders_m"]
        corner = name_corner(center, borders, PrincipalFrame(axis))
        actual = (*vector(fields["display_root"]), *(fields[f"b{i}"] for i in range(4)), *vector(node["f6c0"]))
        require(pack("<10d", *actual) == pack("<10d", *center, *borders, *corner), "native saved display or name location differs")
        displays[name]["name_location_m"] = corner
    return {**pin, **streams, "principal_displays": displays}


def audit(trial, destination):
    require(trial.name == TRIAL, "expected only the disclosed completed trial")
    packet = trial / "Packet"
    frozen = verify(packet, TRIAL_PIN)
    case = json.loads((packet / "Case.json").read_bytes())
    out = trial / "DisclosedTrial"
    result = json.loads(checked(out / "Result.json", RESULT_PIN))
    require(result["schema"] == SCHEMA and result["trial_sha256"] == TRIAL_PIN and result["passed"]
            and result["distinct_processes"] == 6 and result["private_inputs_read"] == 0,
            "unqualified disclosed native result")
    first, last = [control(out, result["controls"][side], side) for side in ("before", "after")]
    rows = {label: phase(out, entry, label, case["tree"]) for label, entry in result["phases"].items()}
    observed = [first, *(rows[name + "-" + role]["process"] for name in ARMS for role in ("edit", "reopen")), last]
    require(len(rows) == 4 and observed == sorted(set(observed)), "wrong number, process identity or sequence")
    all_diagonals = {}
    max_error = 0.0
    for stage in ("edit", "reopen"):
        left, right = (rows[name + "-" + stage]["displays"] for name in ARMS)
        require(left.keys() == right.keys(), "different phase stage inventory")
        for checkpoint, displays in left.items():
            for name, row in displays.items():
                expected = right[checkpoint][name]["actual_m"]
                require(pack("<6d", *(num for point in row["actual_m"] for num in point))
                        == pack("<6d", *(num for point in expected for num in point)), "live feature presentation differs by arm")
                max_error = max(max_error, row["nearest_error_m"], right[checkpoint][name]["nearest_error_m"])
        all_diagonals[stage] = {checkpoint: {name: row["actual_m"] for name, row in displays.items()} for checkpoint, displays in left.items()}
    saved = {}
    for arm in frozen["arms"]:
        name = arm["name"]
        edited, reopened = (rows.pop(name + "-" + role) for role in ("edit", "reopen"))
        require(edited["source_path"] == frozen["native_locator"] and edited["source_sha256"] == arm["sha256"]
                and reopened["source_sha256"] == edited["saved"]["sha256"], "native phases did not use the exact common or derived archive")
        for entry in (edited, reopened):
            entry.pop("source_path")
            entry.pop("displays")
        request = json.loads(checked(packet / (name + "-Neutral.json"), arm["request_sha256"]))
        plan = ProjectPlain(FromData(request["document"]))
        box = (ORIGIN, (plan.WidthValue, plan.HeightValue, case["edit"]["new_depth_m"]))
        saved[name] = {"edit": edited, "reopen": reopened, "replayed_saved": saved_presentation(out / (name + "-edit") / "Edited.SLDPRT", edited["saved"], box)}
    total = sum(len(rows) for stages in all_diagonals.values() for rows in stages.values())
    require(total == 10 and not any(name in ("Swapp", "pythoncom", "pywintypes") or name.startswith("win32com") for name in sys.modules),
            "unexpected display comparison count or host CAD import")
    value = {"schema": "kit.sw2026.principal-datum-display-contrast.native-evidence.v1", "native_result_sha256": RESULT_PIN,
             "trial_sha256": TRIAL_PIN, "controls": result["controls"], "native_processes": len(observed),
             "exact_display_pairs": total, "individual_native_display_observations": total * 2, "max_numeric_corner_error_m": max_error,
             "shared_diagonals": all_diagonals, "arms": saved,
             "native_checks": sum(value[role]["numeric_checks"] for value in saved.values() for role in ("edit", "reopen")),
             "part_tree_rows": len(case["tree"]),
             "same_observable_display_from_first_query": True, "load_vs_first_getter_update_order_measured": False,
             "dependent_axis_measured": False, "held_out_credit": 0, "host_native_launches": 0,
             "audit_sha256": digest(HERE.read_bytes())}
    with destination.open("xb") as file:
        file.write(encode(value))
    print(digest(destination.read_bytes()))


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--trial", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    audit(args.trial, args.output)
