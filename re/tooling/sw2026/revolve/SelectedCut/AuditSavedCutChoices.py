from argparse import ArgumentParser
from dataclasses import asdict
from hashlib import sha256
from math import isclose
from pathlib import Path
from types import SimpleNamespace
import json
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[5]
sys.path[:0] = [str(ROOT / "src"), str(HERE.parent), str(HERE.parent.parent / "EndModes")]

from AuditRevEndOwners import audit_streams
from ProveSelectedRevCut import BUILD, LOCK, checked, need
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadPrincAxis import ReadPrincAxis
from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import PrincipalFrame
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.Revolves.SelectedCut.ReadRevBand import ReadRevBand
from convert.adapters.solidworks.Core.TypedResolved.Revolves.SelectedCut.ReadSelRevCut import ReadSelRevCut
from StockCutGeometry import bbox_measure, cut_measure
from StockCutPlan import AnnularSection

PAIR_LOCK = "f3caaecc7fce3f4f2feb50cd09e24b2b2b9ef78779e493d10ac71b950854186b"


def compare(actual, predicted):
    return isclose(actual, predicted, rel_tol=1e-7, abs_tol=1e-11)


def xyz(fields):
    return tuple(fields[key] for key in "xyz")


def compare_measure(actual, predicted):
    return actual["faces"] == predicted.face_count and all(compare(value, expected)
        for value, expected in zip(
            (actual["volume_m3"], actual["area_m2"], *actual["com_m"]),
            (predicted.volume_m3, predicted.area_m2, *predicted.centre_m), strict=True,
        ))


def read_data(root, capture, name, key, pin):
    path = root / capture / "Capture" / name / (name + key)
    return json.loads(checked(path, pin))


def state_rows(root, capture, lock_sha, names, selected_count):
    folder = root / capture / "Capture"
    lock = json.loads(checked(folder / "SourceLock.json", lock_sha))
    need(lock["oracle_build"] == BUILD and lock["idle_after"] and lock["inputs_unchanged"]
         and lock["writer_output_count"] == 0 and lock["distinct_processes"] == (9 if selected_count == 1 else 8),
         "native source custody does not match the disclosed batch")
    processes = []
    for role in ("control-before", "control-after"):
        entry = lock[role]
        phase = json.loads(checked(folder / f"{role}.json", entry["sha256"]))
        need(entry["passed"] and phase["opened"] and phase["open_errors"] == phase["open_warnings"] == 0
             and phase["rebuilt"] and not phase["dialogs"]
             and phase["oracle_identity"]["sha256"] == lock["oracle_sha256"], "native source control failed")
        processes.append(phase["oracle_identity"]["process_creation_filetime"])
    seen = []
    for entry in lock["sources"]:
        name = entry["case"]
        if name not in names:
            need(selected_count == 1 and name == "RevCutAll" and not entry["passed"]
                 and entry["native_sha256"] is None, "unexpected excluded source")
            continue
        need(entry["passed"] and [row["phase"] for row in entry["phases"]] == ["author", "reopen", "edited-reopen"],
             "all disclosed native lifecycle phases are required")
        phases = {}
        for row in entry["phases"]:
            role = row["phase"]
            path_key = ("-edited" if role == "edited-reopen" else "") + f".{role}.json"
            phase = read_data(root, capture, name, path_key, row["sha256"])
            need(phase["passed"] and phase["oracle_identity"]["sha256"] == lock["oracle_sha256"],
                 "disclosed native lifecycle failed")
            processes.append(phase["oracle_identity"]["process_creation_filetime"])
            phases[role] = phase
        seen.append(name)
        original, edited = phases["reopen"], phases["edited-reopen"]
        saved = original["edited_derivative"]
        need(saved["save_status"] == [True, 0, 0], "disclosed edit did not save cleanly")
        for key, pin, phase in (("original", entry["native_sha256"], original), ("edited", saved["sha256"], edited)):
            suffix = "" if key == "original" else "-edited"
            raw = checked(folder / name / (name + suffix + ".SLDPRT"), pin)
            observe = phase["reopened"]["definition"]["scope"]
            need(observe["feature_scope"] and not observe["auto_select"] and observe["array_present"]
                 and observe["count"] == selected_count, "scope is outside disclosed explicit selection")
            yield name, key, pin, SldprtArchive.from_bytes(raw), phase["reopened"]
    need(set(seen) == set(names) and len(processes) == len(set(processes)) == 8
         and all(processes[0] < value < processes[1] for value in processes[2:]),
         "disclosed sources were not bracketed by both controls")


def ids(root, key):
    return [row["o"].FieldsValue["f140"] for row in root.FieldsValue.get(key, {}).get("items", ())]


def wrapper_rows(link):
    cut = link.ResolvedValue.RootsValue[-1]
    roots = link.ResolvedValue.RootsValue[-6:][1::2]
    need([value.ClassValue.NameValue for value in roots] == ["moRevolution_c", "moRevolution_c", "moRevCut_c"]
         and all(value.FieldsValue["f544"] == 1 for value in roots), "unexpected explicit saved body profile")
    summary = []
    for row in cut.FieldsValue["f548"]["items"]:
        item = row["o"]
        data = item.FieldsValue
        picked = data["ff0"].FieldsValue
        need(item.ClassValue.NameValue == "moCompSolidBody_c" and data["f18"] == data["f1c"]
             and data["f110"] == [{"v": data["f18"]}] and data["f58"].FieldsValue["owner"] is link.ConfigValue.RootValue,
             "saved selection row lacks the actual scoped atom lineage")
        keepers = [row["f08"].FieldsValue["f10"]["f10"].FieldsValue["f10"]
                   for row in picked["f10"] if row["f08"] is not None]
        summary.append({"atom": data["f18"], "producer": [value["f00"] for value in keepers],
                        "f108": data["f108"], "f104": data["f104"], "f100": data["f100"],
                        "face": [picked[key] for key in ("f08", "fe8", "f70")]})
    consumed, result = (ids(cut, field) for field in ("f530", "f528"))
    need(sorted(consumed) == sorted(value["atom"] for value in summary) and len(result) == len(summary),
         "actual selected and output arrays differ from measured scope")
    return {"boss_ids": [data.FieldsValue["f08"] for data in roots[:2]],
            "consumed_atoms": consumed, "result_atoms": result, "wrappers": summary}


def compare_single_geometry(archive, link, frame_hint):
    top = ReadHeaderGraph(archive.require("Header2"), 19000)
    proof = ReadSelRevCut(link, top)
    operations = (*proof.StockValues, proof.CutValue)
    angles = [value.AngleValue.RadiansValue for value in operations]
    cut = proof.CutValue
    axis_name = ReadPrincAxis(cut.FrameValue.SupportValue)
    anchor_mm = cut.ProfileGraph.AxisPoints[cut.ProfileGraph.AxisValue.StartValue].PositionValue[0]
    anchor = anchor_mm * 0.001
    sections = tuple(AnnularSection(tuple((value - anchor_mm) * 0.001 for value in section.Radial),
                                    tuple(value * 0.001 for value in section.Axial), {})
                     for section in map(ReadRevBand, operations))
    index = proof.AtomsValue.SelectedIndex
    picked, tool = sections[index], sections[2]
    overlap = (max(picked.radial[0], tool.radial[0]), min(picked.radial[1], tool.radial[1]))
    plan = SimpleNamespace(operations=(None, None, SimpleNamespace(AxisStart=(anchor, 0), AxisValue=axis_name,
                           AngleValue=angles[-1], IsReverse=cut.IsReverse)), sections=sections, selected_index=index,
                           reached_wall=("outer", "inner")[index], radial_overlap=overlap)
    predicted = cut_measure(plan)
    observations = {row["name"]: row for row in frame_hint["measured"].values()}
    observed = tuple(observations[ReadNativeName(value.NodeValue)] for value in (proof.UntouchedValue, cut))
    need(all(compare_measure(first, second) for first, second in zip(observed, predicted, strict=True)),
         "analytic scoped volumes, surface areas, face counts or centroids disagree with disclosed native output")
    boxes = []
    for operation, section in zip(operations, (*sections[:2], picked), strict=True):
        reference = operation.NodeValue.FieldsValue["f4a8"]["f48"]["items"][0]["o"].FieldsValue
        actual = reference["f48"]["items"][0]["o"].FieldsValue
        centre, diag = bbox_measure(anchor, PrincipalFrame(axis_name), section)
        need(actual["f08"] == 1 and all(compare(value, target) for value, target
                                     in zip((*xyz(actual["f10"]), actual["f28"]), (*centre, diag), strict=True)),
             "analytic chooser bound disagrees with disclosed typed owner")
        boxes.append({"centre_m": centre, "diagonal_m": diag})
    return {"axis": axis_name, "angle_radians": angles, "chooser_bounds": boxes,
            "predicted": [asdict(value) for value in predicted],
            "observed": [{"volume_m3": value["volume_m3"], "area_m2": value["area_m2"],
                          "centre_m": value["com_m"], "face_count": value["faces"]} for value in observed]}


def audit(root):
    experiments = []
    for capture, lock, names, count in (("RevolveCutDiscovery03", LOCK, ("RevCutInner", "RevCutOuter"), 1),
                                        ("RevolveCutBothDiscovery01", PAIR_LOCK, ("ScopePairA", "ScopePairB"), 2)):
        for name, phase, pin, archive, measurement in state_rows(root, capture, lock, names, count):
            link = ReadNativeLink(archive, 0)
            data = wrapper_rows(link)
            if count == 1:
                data["analytic_comparison"] = compare_single_geometry(archive, link, measurement)
            experiments.append({"case": name, "phase": phase, "sha256": pin, "capture_sha256": lock,
                                "linked_replay": audit_streams(archive, link), "measurements": data})
    return {"schema": "kit.sw2026.disclosed-revolve-cut-storage-contrast.v1",
            "tool_sha256": sha256(HERE.read_bytes()).hexdigest(), "cases": experiments,
            "native_processes_started": 0, "heldout_inputs_read": 0, "writer_output_count": 0}


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--published-captures", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    payload = (json.dumps(audit(arguments.published_captures), sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    with arguments.output.open("xb") as stream:
        stream.write(payload)
    print(sha256(payload).hexdigest())
