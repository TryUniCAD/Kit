import json
import sys
import time
from math import isclose
from pathlib import Path, PureWindowsPath
from shutil import copyfile

from AuthorCurves import digest, require, write_json
from InspectPartitionOpen import HELPERS, MODES, PART, run_phase


VARIANTS = ("WithoutPartition", "WithAttachment")


def prepare(job):
    require(job["schema"] == "kit.sw2026.rectangle-partition-open-job.v1", "unexpected rectangle partition job")
    stage, control, checkout = (Path(job[key]).resolve(strict=True) for key in ("stage", "control", "checkout_root"))
    output = Path(job["output"]).resolve()
    active = stage / "Active"
    require(all(not path.is_relative_to(checkout) for path in (stage, control, output)), "probe inputs and output must stay outside the checkout")
    require(not output.exists() and not active.exists() and digest(control) == job["control_sha256"], "probe output already exists or control digest differs")
    lock = stage / "Freeze.json"
    require(digest(lock) == job["freeze_sha256"], "offline generation receipt digest differs")
    frozen = json.loads(lock.read_bytes())
    require(frozen["schema"] == "kit.sw2026.rectangle-populated-attachment-discovery.v1" and frozen["heldout_acceptance"] is False,
            "probe requires the frozen rectangle discovery pair")
    require(PureWindowsPath(active / PART) == PureWindowsPath(frozen["native_path"]), "probe must use the originally encoded guest path")
    require(set(frozen["variants"]) == set(VARIANTS) and len(set(frozen["variants"].values())) == 2, "probe needs two distinct variants")
    sources = {variant: stage / variant / PART for variant in VARIANTS}
    for variant, source in sources.items():
        require(source.resolve(strict=True) == source and digest(source) == frozen["variants"][variant], "frozen child does not match")
    return active, control, output, sources, frozen


def geometry_match(state, expected):
    if state is None or state["body_count"] != 1 or state["mass"] is None:
        return False
    body, = state["bodies"]
    mass = state["mass"]
    actual = (mass["volume"], mass["area"], *mass["com"])
    target = (expected["signed_volume_mm3"] / 1e9, expected["area_mm2"] / 1e6, *(value / 1000 for value in expected["center_mm"]))
    return (state["before_geometry"] == state["after_geometry"]
            and state["before_geometry"]["needs_rebuild"] == state["before_geometry"]["whats_wrong"] == 0
            and body["faces"] == len(body["face_owners"]) == 6
            and all(owner == {"name": "Boss-Extrude1", "type": "Extrusion"} for owner in body["face_owners"])
            and all(isclose(a, b, rel_tol=2e-7, abs_tol=1e-15) for a, b in zip(actual, target, strict=True)))


def execute(job, job_path, active, control, output, sources, frozen):
    from InspectFresh import healthy, inspect

    output.mkdir(parents=True, exist_ok=False)
    tools = (Path(__file__).name, "InspectPartitionOpen.py", *HELPERS)
    report = {
        "schema": "kit.sw2026.rectangle-partition-open-observations.v1", "job_sha256": digest(job_path),
        "freeze_sha256": job["freeze_sha256"], "tool_sha256": {name: digest(Path(__file__).with_name(name)) for name in tools},
        "started_at": time.time(), "controls": [], "phases": [], "heldout_acceptance": False,
    }

    def checkpoint():
        write_json(output / "Inspection.json", report)

    def control_phase(label):
        row = {"kind": label}
        report["controls"].append(row)
        inspect(control, result=row, checkpoint=checkpoint)
        row["healthy"] = bool(healthy(row) and row.get("sha256") == job["control_sha256"]
                              and row.get("oracle_identity", {}).get("sha256") == job["oracle_sha256"])
        checkpoint()
        return row["healthy"]

    try:
        if control_phase("before"):
            for variant, source in sources.items():
                active.mkdir()
                target = active / PART
                try:
                    copyfile(source, target)
                    require(digest(target) == frozen["variants"][variant], "active copy differs from its frozen digest")
                    row = run_phase(job, output, active, variant, MODES[0])
                    row["after_open_geometry_matches"] = geometry_match(row.get("after_open", {}).get("child"), frozen["geometry"])
                    row["after_rebuild_geometry_matches"] = geometry_match(row.get("after_rebuild", {}).get("child"), frozen["geometry"])
                    report["phases"].append(row)
                    require(digest(target) == frozen["variants"][variant], "open/rebuild operation changed the active file")
                    checkpoint()
                finally:
                    active.rename(output / (variant + "Copy"))
    except Exception as error:
        report["exception"] = repr(error)
    finally:
        try:
            control_phase("after")
        except Exception as error:
            report["control_after_exception"] = repr(error)
        report["controls_healthy"] = [row.get("healthy", False) for row in report["controls"]] == [True, True]
        identities = [row.get("oracle_identity", {}).get("process_creation_filetime") for row in (*report["controls"], *report["phases"])]
        report["distinct_processes"] = len({identity for identity in identities if type(identity) is int and identity > 0})
        report["inputs_immutable"] = (digest(control) == job["control_sha256"]
                                      and all(digest(source) == frozen["variants"][variant] for variant, source in sources.items()))
        report["diagnostic_completed"] = bool(report["controls_healthy"] and report["inputs_immutable"]
                                              and len(identities) == report["distinct_processes"] == 4
                                              and "exception" not in report and all(row["completed"] for row in report["phases"]))
        report["both_clean_open_and_rebuild"] = bool(report["diagnostic_completed"] and all(
            row.get("open_status") == [True, 0, 0] and row.get("after_open_geometry_matches")
            and row.get("rebuild_return") and row.get("after_rebuild_geometry_matches") for row in report["phases"]
        ))
        report["finished_at"] = time.time()
        checkpoint()
    print(json.dumps({key: report[key] for key in ("diagnostic_completed", "controls_healthy", "distinct_processes", "both_clean_open_and_rebuild")}))
    return int(not report["diagnostic_completed"])


if __name__ == "__main__":
    job_path = Path(sys.argv[1]).resolve(strict=True)
    job = json.loads(job_path.read_bytes())
    raise SystemExit(execute(job, job_path, *prepare(job)))
