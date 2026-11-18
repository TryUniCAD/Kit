from __future__ import annotations

import argparse
import json
import os
from pathlib import Path, PureWindowsPath
from shutil import copyfileobj

from AuthorCurves import digest, require, write_json
from AuthorRectangleAnchors import CONTROL, ORACLE, control
from InspectSdkBlindPart import TOOLS as PART_TOOLS, phase, tree_prediction


SCHEMA = "kit.sw2026.sdk-original-polygon-cohort.v1"
LOCK = "abc1724a8856083a9c5e7054cd85b3035dc7da8423063f0caabd07a3e6f9dc40"
SLOTS = ("H3_scalene", "H5_irregular", "H7_irregular")
TOOLS = (*PART_TOOLS, Path(__file__).name)


def checked(path, sha):
    require(path.is_file() and digest(path) == sha, f"frozen evidence changed: {path.name}")
    return path


def verify(packet, expected):
    root = packet.parent
    job = json.loads(checked(packet, expected).read_bytes())
    require(job["schema"] == SCHEMA and job["oracle_sha256"] == ORACLE and job["source_lock_sha256"] == LOCK,
            "expected the exact original held-out polygon trial")
    tools = root / "Tools"
    require(Path(__file__).resolve().parent == tools and set(job["tools_sha256"]) == set(TOOLS),
            "the polygon trial observer closure differs")
    for name, sha in job["tools_sha256"].items():
        checked(tools / name, sha)
    seed = checked(root / "Control.SLDPRT", CONTROL)
    locked = json.loads(checked(root / "SourceLock.json", LOCK).read_bytes())
    locks = {Path(row["name"]).stem: row for row in locked["records"] if row["kind"] == "held-out"}
    generation = json.loads(checked(root / "Generation.json", job["generation_sha256"]).read_bytes())
    require(generation["passed"] and generation["source_lock_sha256"] == LOCK and generation["original_native_files_read"] == 0
            and tuple(row["slot"] for row in generation["cases"]) == SLOTS == tuple(locks),
            "the original native sources cannot be opened before all three SDK outputs are frozen")
    plans = []
    for row in generation["cases"]:
        slot = row["slot"]
        folder = root / slot
        case = json.loads(checked(folder / "Expected.json", row["expected_sha256"]).read_bytes())
        request = json.loads(checked(folder / "NeutralRequest.json", row["request_sha256"]).read_bytes())
        candidate = checked(folder / "Candidate.SLDPRT", row["generated_sha256"])
        source = locks[slot]
        encoded = PureWindowsPath(case["intent"]["self_path"])
        require(encoded.name == source["name"] and encoded.parent == PureWindowsPath(r"C:\KitSdkCandidates"),
                "the neutral polygon's stored self identity changed")
        require(source["sha256"] == row["original_source_sha256"] == case["source_native_sha256"]
                and source["bytes"] == case["source_native_bytes"] and candidate.stat().st_size == row["bytes"]
                and row["build_a_sha256"] == row["build_b_sha256"] and row["streams"] == 10
                and row["runtime_input_reads"] == 0 and row["guarded_workers"] == 4,
                "generation, source and exact neutral fixture evidence disagree")
        plans.append((source, row, case, candidate, tree_prediction(request, case)))
    return job, seed, plans


def run(packet, packet_sha):
    require(os.name == "nt", "original polygon sources may be opened only in the pinned guest")
    job, seed, plans = verify(packet, packet_sha)
    originals = Path(job["original_sources"]).resolve(strict=True)
    require(originals.is_dir(), "the directory containing the pre-writer held-out sources is unavailable")
    output = packet.parent / "Inspection"
    output.mkdir()
    result = {"schema": SCHEMA, "packet_sha256": packet_sha, "generation_sha256": job["generation_sha256"],
              "source_lock_sha256": LOCK, "phases": {}, "cases": [], "passed": False}
    stages = result["phases"]

    def checkpoint():
        write_json(output / "Result.json", result)

    def record(role, argument, *inputs, **options):
        stages[role] = argument(output, role, *inputs, **options)
        checkpoint()
        return stages[role]

    before = None
    try:
        before = record("ControlBefore", control, seed)
        if before["passed"]:
            for source, row, case, candidate, tree in plans:
                slot = row["slot"]
                native = checked(originals / source["name"], source["sha256"])
                require(native.stat().st_size == source["bytes"], "the locked native file has the wrong extent")
                staged = Path(case["intent"]["self_path"])
                staged.parent.mkdir(exist_ok=True)
                with candidate.open("rb") as inp, staged.open("xb") as out:
                    copyfileobj(inp, out)
                require(digest(staged) == row["generated_sha256"], "staged generated part differs before native open")
                reference = record(slot + "Source", phase, native, source["sha256"], case, tree, measure_only=True)
                built = record(slot + "Generated", phase, staged, row["generated_sha256"], case, tree)
                reopened = None
                if built["passed"]:
                    saved = output / (slot + "Generated") / "Edited.SLDPRT"
                    reopened = record(slot + "Reopen", phase, saved, built["derivative_sha256"], case, tree,
                                      edited_tree=built["states"]["Edited"]["tree"])
                parity = reference["passed"] and built["passed"] and reference["states"]["Rebuilt"]["tree"] == built["states"]["Rebuilt"]["tree"]
                result["cases"].append({"slot": slot, "native_source_tree_parity": parity, "source_immutable": digest(native) == source["sha256"],
                                        "generated_immutable": digest(staged) == row["generated_sha256"],
                                        "passed": bool(parity and reopened and reopened["passed"])})
                checkpoint()
    except Exception as error:
        result["error"] = repr(error)
    finally:
        after = record("ControlAfter", control, seed)
        verified, _, _ = verify(packet, packet_sha)
        distinct = {phase_value["oracle_identity"]["process_creation_filetime"] for phase_value in stages.values()
                    if phase_value.get("oracle_identity")}
        controls = bool(before and before["passed"] and after["passed"])
        result.update(controls_healthy=controls, method_unchanged=verified == job, distinct_processes=len(distinct),
                      original_source_files_consulted=len(result["cases"]))
        result["passed"] = (controls and result["method_unchanged"] and len(stages) == len(distinct) == 11
                            and len(result["cases"]) == 3 and all(row["passed"] and row["source_immutable"]
                            and row["generated_immutable"] for row in result["cases"]))
        checkpoint()
    return result


def main():
    parser = argparse.ArgumentParser(description="Compare the complete SDK polygon writer with the original locked SOLIDWORKS sources")
    parser.add_argument("command", choices=("verify", "run"))
    parser.add_argument("packet", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    args = parser.parse_args()
    packet = args.packet.resolve(strict=True)
    if args.command == "verify":
        verify(packet, args.packet_sha256)
        print('{"passed": true, "original_native_sources_read": 0}')
        return 0
    result = run(packet, args.packet_sha256)
    print(json.dumps({key: result[key] for key in ("passed", "controls_healthy", "distinct_processes")}, sort_keys=True))
    return 0 if result["passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
