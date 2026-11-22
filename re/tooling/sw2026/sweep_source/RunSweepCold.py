from argparse import ArgumentParser
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from RunSweepSources import CONTROLS, launch
from SweepColdCompare import lifecycle
from SweepColdPacket import FILES, local_roots, stage, verify
from SweepModel import DRIVERS, PHASES, require
from SweepPacket import BUILD, ORACLE, digest, valid_hash, write_new


PHASES = ("candidate-open", *PHASES[1:])


def members(packet, capture, slot, case):
    folder = capture / f"Slot{slot + 1:02d}"
    original = packet / "Candidates" / (case["name"] + ".SLDPRT")
    derivatives = {role: folder / (case["name"] + role.title() + "Edit.SLDPRT") for role in DRIVERS}
    return folder, original, derivatives


def worker(args):
    job, spec, predictions = verify(args.job, args.pin)
    packet, capture = local_roots(args.job, job)
    if args.phase in CONTROLS:
        require(args.slot is args.source is None, "control cannot name a candidate")
        folder = capture / args.phase
    else:
        require(type(args.slot) is int and 0 <= args.slot < len(spec["cases"]) and valid_hash(args.source),
                "missing exact cold phase source")
        case = spec["cases"][args.slot]
        base, original, derivatives = members(packet, capture, args.slot, case)
        folder = base / args.phase
        role, _, action = args.phase.partition("-")
        if action != "reopen":
            relative = original.relative_to(packet).as_posix()
            require(args.source == job["files"][relative]["sha256"], "wrong immutable generated input")
    auth = {"phase": args.phase, "slot": args.slot, "source_sha256": args.source, "job_sha256": args.pin}
    record = folder / "Record.json"
    require(folder.resolve() == folder and not record.exists()
            and json.loads((folder / "Phase.json").read_bytes()) == auth, "cold phase has no supervisor authorization")
    if args.phase in CONTROLS:
        from FilletSourcePhase import run_control
        return run_control(packet / "Control.SLDPRT", record)
    import Swapp
    from SweepApi import inspect_registration
    constants, api = inspect_registration(Swapp)
    require(api == json.loads((packet / "ExpectedApi.json").read_bytes()), "registered COM differs from independent source")
    plan = predictions[case["name"]]
    density = spec["density_kg_m3"]
    if args.phase == "candidate-open":
        from SweepColdPhase import run_cold
        return run_cold(case, plan["original"], density, original, args.source, record, constants)
    from SweepPhase import run_native
    return run_native(case, plan, density, args.phase, original, derivatives, args.source, record, constants)


def run_case(manifest, pin, job, packet, capture, slot, case, comparison, processes):
    folder, original, derivatives = members(packet, capture, slot, case)
    original_pin = job["files"][original.relative_to(packet).as_posix()]["sha256"]
    require(digest(original) == original_pin and slot == comparison["slot"], "wrong frozen candidate pairing")
    phases, records = [], {}
    for phase in PHASES:
        role, _, action = phase.partition("-")
        source = records[f"{role}-edit"]["native_sha256"] if action == "reopen" else original_pin
        row, record = launch(manifest, pin, folder / phase, phase, processes, slot, source, runner=Path(__file__).resolve())
        phases.append(row)
        records[phase] = record
        if not row["passed"]:
            return {"slot": slot, "phases": phases, "passed": False}
    try:
        props = lifecycle(original, derivatives, records, comparison["states"])
    except ValueError as error:
        write_new(folder / "PairedFailure.json", {"error": str(error)})
        return {"slot": slot, "phases": phases, "passed": False, "paired_failure": True}
    return {"slot": slot, "phases": phases, "passed": True,
            "independent_source_sha256": comparison["native_source_sha256"],
            "independent_observer_sha256": comparison["source_receipt_sha256"], **props}


def execute(manifest, pin):
    job, spec, _ = verify(manifest, pin)
    packet, capture = local_roots(manifest, job)
    import Swapp
    require(not capture.exists() and not Swapp.application_pids() and not Swapp.owned_process_ids(),
            "native sweep requires fresh results and an idle oracle")
    capture.mkdir()
    comparisons = json.loads((packet / "DisclosedComparison.json").read_bytes())
    require(comparisons["source_lock_sha256"] == job["source_lock_sha256"]
            and len(comparisons["cases"]) == len(spec["cases"]), "missing independent source lock")
    processes, controls, cases = [], {}, []
    runner = Path(__file__).resolve()
    try:
        before, _ = launch(manifest, pin, capture / CONTROLS[0], CONTROLS[0], processes, runner=runner)
        controls["before"] = before
        if before["passed"]:
            for slot, (case, comparison) in enumerate(zip(spec["cases"], comparisons["cases"], strict=True)):
                cases.append(run_case(manifest, pin, job, packet, capture, slot, case, comparison, processes))
    except Exception as error:
        write_new(capture / "BatchFailure.json", {"error": repr(error)})
    finally:
        try:
            controls["after"], _ = launch(manifest, pin, capture / CONTROLS[1], CONTROLS[1], processes, runner=runner)
        except Exception as error:
            controls["after"] = {"passed": False}
            write_new(capture / "AfterControlFailure.json", {"error": repr(error)})
    unchanged = verify(manifest, pin)[0] == job
    idle = not Swapp.application_pids() and not Swapp.owned_process_ids()
    count = len(processes)
    distinct = len(set(processes))
    result = {"schema": "kit.sw2026.standard-sweep-cold-result.v1", "job_sha256": pin, "oracle_build": BUILD,
              "oracle_sha256": ORACLE, "writer_revision": job["writer_revision"], "source_lock_sha256": job["source_lock_sha256"],
              "cases": cases, "controls": controls, "idle_after": idle, "inputs_unchanged": unchanged,
              "distinct_processes": distinct, "started_processes": count, "heldout_credit": 0}
    result["passed"] = bool(idle and unchanged and count == distinct == len(PHASES) * len(spec["cases"]) + len(CONTROLS)
                            and len(cases) == 2 and all(case["passed"] for case in cases)
                            and all(controls.get(role, {}).get("passed") for role in ("before", "after")))
    report = capture / "Result.json"
    write_new(report, result)
    return {"result_sha256": digest(report), "passed": result["passed"], "distinct_processes": distinct,
            "cases_passed": sum(case["passed"] for case in cases)}


def main():
    parser = ArgumentParser(description="Compare model-only candidates with exact disclosed native source lifecycles")
    parser.add_argument("--job", type=Path, required=True)
    parser.add_argument("--pin", required=True)
    parser.add_argument("--slot", type=int)
    parser.add_argument("--source")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--verify-packet", action="store_true")
    modes.add_argument("--stage-guest", action="store_true")
    modes.add_argument("--phase", choices=(*PHASES, *CONTROLS))
    args = parser.parse_args()
    if args.phase:
        return int(not worker(args))
    if args.stage_guest:
        status = stage(args.job, args.pin)
    elif args.verify_packet:
        verify(args.job, args.pin)
        status = {"job_sha256": args.pin, "bound_files": len(FILES), "native_processes": 0}
    else:
        status = execute(args.job, args.pin)
    print(json.dumps(status, sort_keys=True, allow_nan=False))
    return int(not status.get("passed", True))


if __name__ == "__main__":
    raise SystemExit(main())
