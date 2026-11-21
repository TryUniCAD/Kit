from argparse import ArgumentParser
from pathlib import Path
import json
import os
import time

from PatternDatumHeightPacket import (
    BUILD, CASE_NAMES, CONTROL, ORACLE, PHASES, SPEC, arm_spec, artifact_name,
    digest, require, verified_plan, verify,
)
from RunPatternEnvelope import inspect_phase, installed, saved_hash


RESULT_SCHEMA = "kit.sw2026.linear-pattern-datum-height-native.v1"


def registered(packet):
    import Swapp
    from AuthorPatternDatumHeight import bounds_metadata

    report = installed(packet)
    report["datum_bounds"] = bounds_metadata(report["angle"])
    require(not Swapp.application_pids(), "display property metadata started a CAD process")
    return report


def run(root, packet, pin, manifest, report):
    import Swapp
    from AuthorCurves import write_json
    from AuthorLinearPatternSources import control_phase
    from AuthorPatternDatumHeight import PatternDatumHeightAuthor

    out = root / "DisclosedHeights"
    out.mkdir(exist_ok=False)
    path = out / "Result.json"
    metadata = out / "RegisteredApi.json"
    write_json(metadata, report)
    spec = verified_plan(packet / "Spec.json")
    processes = []
    result = {
        "schema": RESULT_SCHEMA, "cohort": "disclosed", "native_build": BUILD,
        "oracle_sha256": ORACLE, "packet_sha256": pin, "research_revision": manifest["research_revision"],
        "spec_sha256": SPEC, "metadata_sha256": digest(metadata.read_bytes()),
        "controls": {}, "phases": [], "artifacts": {}, "application_pids_before": sorted(Swapp.application_pids()),
        "started_at": time.time(), "native_lifecycle_passed": False, "writer_output_count": 0,
        "heldout_sources_accessed": 0,
    }
    write_json(path, result)

    def control(side):
        if Swapp.application_pids():
            result["controls"][side] = {"passed": False, "reason": "prior oracle process still running"}
            return
        receipt, identity = control_phase(packet / "Control.SLDPRT", CONTROL, out / ("Control" + side.title() + ".json"))
        result["controls"][side] = receipt
        if identity is not None:
            processes.append(identity)
        write_json(path, result)

    def candidate(case):
        home = out / case
        home.mkdir(exist_ok=False)
        target = home / artifact_name(case)
        shape = arm_spec(spec, case)
        original = None
        for phase in PHASES:
            data, row = inspect_phase(home, phase, shape, report, target, None, original, None,
                                      author_type=PatternDatumHeightAuthor)
            result["phases"].append({"case": case, **row})
            if identity := data.get("oracle_identity"):
                processes.append(identity["process_creation_filetime"])
            if row["passed"] and phase == "author":
                result["artifacts"][case] = original = data["artifact"]
            write_json(path, result)
            if not row["passed"]:
                return False
        return True

    try:
        require(not result["application_pids_before"], "datum height trial requires an idle oracle")
        control("before")
        if result["controls"]["before"]["passed"]:
            for case in CASE_NAMES:
                if not candidate(case):
                    break
    except Exception as error:
        result["failure"] = repr(error)
    finally:
        control("after")
        result["application_pids_after"] = sorted(Swapp.application_pids())
        result["finished_at"] = time.time()
        result["distinct_processes"] = len(set(processes))
        result["process_creation_filetimes"] = processes
        try:
            verify(packet, pin)
            result["packet_unchanged"] = True
            artifacts = result["artifacts"]
            require(set(artifacts) == set(CASE_NAMES)
                    and all(saved_hash(out / case / artifact_name(case)) == artifacts[case] for case in CASE_NAMES)
                    and len({item["sha256"] for item in artifacts.values()}) == 2, "incomplete or changed native output")
            result["artifacts_unchanged"] = True
        except Exception as error:
            result["final_binding_failure"] = repr(error)
        result["native_lifecycle_passed"] = bool(
            set(result["controls"]) == {"before", "after"} and all(row["passed"] for row in result["controls"].values())
            and [[row["case"], row["phase"]] for row in result["phases"]] == manifest["sequence"]
            and all(row["passed"] for row in result["phases"])
            and len(processes) == 6 and sorted(set(processes)) == processes
            and not result["application_pids_before"] and not result["application_pids_after"]
            and result.get("packet_unchanged") and result.get("artifacts_unchanged") and "failure" not in result
        )
        write_json(path, result)
    print(json.dumps({"native_lifecycle_passed": result["native_lifecycle_passed"],
                      "distinct_processes": result["distinct_processes"],
                      "process_result_sha256": digest(path.read_bytes())}))
    return int(not result["native_lifecycle_passed"])


def main():
    parser = ArgumentParser()
    parser.add_argument("--pin", required=True)
    args = parser.parse_args()
    require(os.name == "nt", "datum-height metadata and native observation require the root-owned Windows oracle")
    packet = Path(__file__).resolve().parents[1]
    manifest = verify(packet, args.pin)
    root = Path(manifest["guest_trial_root"])
    require((root / "Packet").resolve() == packet and not (root / "DisclosedHeights").exists(),
            "native run requires its exact unused datum-height locator")
    return run(root, packet, args.pin, manifest, registered(packet))


if __name__ == "__main__":
    raise SystemExit(main())
