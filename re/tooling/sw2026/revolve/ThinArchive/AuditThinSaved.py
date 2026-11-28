from argparse import ArgumentParser
import json
from pathlib import Path
from subprocess import run
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[5]
sys.path[:0] = [str(ROOT / "src"), str(HERE.parent), str(HERE.parents[1] / "PrincipalReader"),
                str(HERE.parents[1] / "EndModes"), str(HERE.parents[2])]

from AuditPrincipalReader import make_guard
from AuditRevEndOwners import ReadNativeLink, SldprtArchive, digest, require
from ProveTwoDirectionRevolves import warm
from RevolveFamilyModel import edited_case
from ThinSavedCases import BASELINES, cold_input, load_baseline, source_input
from ThinSavedFaults import assert_faults
from ThinSavedRead import assert_cold, read_saved


def folders(home, group):
    if group == "front":
        parent = home / "SdkThinGenerated01"
        return home / "RevolveThinDiscovery01" / "Capture", parent / "Packet", parent / "NativeResult.json"
    parent = home / "SdkThinPlaneGenerated01"
    return home / "RevolveThinPlaneDiscovery01" / "Capture", parent / "Packet", parent / "TerminalResult.json"


def worker(home, group, name, query):
    capture, packet, terminal = folders(home, group)
    _, rows, cases, build, generated = load_baseline(capture, packet, terminal, group)
    edited = query != "original"
    case = dict(cases[name], family="thin")
    mode = BASELINES[group][1][name]
    if query == "cold":
        candidate, pin, locator, epoch = cold_input(packet, build, name, group)
    elif query == "faults":
        original, _, _ = source_input(capture, rows[name], mode, False)
        derivative, _, _ = source_input(capture, rows[name], mode, True)
        alternate_capture, other_packet, other_terminal = folders(home, "principal")
        _, alternatives, _, _, _ = load_baseline(alternate_capture, other_packet, other_terminal, "principal")
        alternate, _, _ = source_input(alternate_capture, alternatives["ThinTopOppositeControl"], 1, False)
    else:
        raw, pin, native = source_input(capture, rows[name], mode, edited)
        require(rows[name]["native_sha256"] == generated[name]["source_sha256"],
                "source capture differs from prior native writer comparison")
    warm()
    gate, guard = make_guard(ROOT / "src")
    if query == "cold":
        return assert_cold(candidate, case, locator, epoch, pin, ROOT, gate, guard)
    gate["enabled"] = True
    try:
        if query == "faults":
            result = assert_faults(derivative, original, alternate)
        else:
            archive = SldprtArchive.from_bytes(raw)
            link = ReadNativeLink(archive, 0)
            result = read_saved(raw, archive, link, native, edited_case(case) if edited else case)
            result["source_sha256"] = pin
    finally:
        gate["enabled"] = False
    require(not guard["unexpected_attempts"], "saved part accessed an external file or program")
    require(not any(name == "Swapp" or name == "pythoncom" or name.startswith("win32com") for name in sys.modules),
            "offline reader unexpectedly imported a native runtime")
    return result | {"guard": guard}


def batch(home, report):
    results = {}
    for group, notes in BASELINES.items():
        lock, rows, _, _, _ = load_baseline(*folders(home, group), group)
        proofs = {}
        for name in rows:
            proofs[name] = {role: launch(home, group, name, role) for role in ("original", "edited", "cold")}
        results[group] = {
            "source_lock_sha256": notes[0], "source_oracle_build": lock["oracle_build"],
            "source_oracle_sha256": lock["oracle_sha256"], "source_authoring_revision": lock["source_revision"],
            "controls": {label: lock[label] for label in ("control-before", "control-after")},
            "source_processes": lock["distinct_processes"], "cold_native_terminal_sha256": notes[-1],
            "cold_build_sha256": notes[-2], "source_model_spec_sha256": lock["spec_sha256"],
            "cases": proofs,
        }
    if report:
        faults = launch(home, "front", "ThinOne", "faults")
        rows = [pair for group in results.values() for pair in group["cases"].values()]
        saved = [pair[role] for pair in rows for role in ("original", "edited")]
        tools = (HERE.name, "ThinSavedCases.py", "ThinSavedFaults.py", "ThinSavedRead.py")
        output = {
            "schema": "kit.sw2026.thin-native-saved-read.v1", "results": results,
            "faults": faults, "host_disclosed_processes": len(rows) + len(saved) + 1,
            "qualified_saved_reads": sum("strict_default_document_sha256" in row
                                         and "strict_semantic_document_sha256" in row for row in saved) * 2,
            "exact_saved_config_and_resolved_streams": sum(len(row["streams"]) for row in saved),
            "proof_tool_sha256": {name: digest((HERE.parent / name).read_bytes()) for name in tools},
            "native_execution": False, "new_heldout_results": 0,
        }
        with report.open("x", encoding="utf-8") as stream:
            json.dump(output, stream, indent=2, sort_keys=True, allow_nan=False)
            print(file=stream)
        print(f"{output['qualified_saved_reads']} native save reads, {len(rows)} unchanged cold writer outputs")


def launch(home, group, name, role):
    done = run((sys.executable, "-B", str(HERE), "--home", str(home), "--worker", group, name, role),
               capture_output=True, text=True, timeout=90)
    require(not done.returncode and not done.stderr, f"{group}/{name}/{role}: {done.stderr}")
    return json.loads(done.stdout)


def main():
    parser = ArgumentParser()
    parser.add_argument("--home", type=Path, required=True)
    direction = parser.add_mutually_exclusive_group(required=True)
    direction.add_argument("--report", type=Path)
    direction.add_argument("--worker", nargs=3)
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(worker(args.home, *args.worker), allow_nan=False, sort_keys=True))
    else:
        batch(args.home, args.report)


if __name__ == "__main__":
    main()
