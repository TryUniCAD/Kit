from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from shutil import copyfile

from AuthorCurves import digest, require, write_json
from InspectDimensionedAssembly import compare_scenes, measured_phase
from InspectFresh import healthy, inspect


VARIANTS = ("WithoutPartition", "WithPartition")
PART = "PartitionProbeChild.SLDPRT"
ASSEMBLY = "L1Single.SLDASM"


def prepare(job, checkout):
    stage, control, output = (Path(job[key]).resolve() for key in ("stage", "control", "output"))
    require(all(not path.is_relative_to(checkout) for path in (stage, control, output)), "native cache measurements must stay outside the checkout")
    require(digest(control) == job["control_sha256"], "control digest differs")
    active = stage / "Active" / "L1Single"
    require(not active.exists() and not output.exists(), "native cache probe output is already occupied")
    sources = {}
    for variant in VARIANTS:
        directory = stage / "L1Single" / variant
        paths = {name: directory / name for name in (ASSEMBLY, PART)}
        for name, path in paths.items():
            require(path.resolve().parent == directory and digest(path) == job["variants"][variant][name], "frozen variant artifact does not match")
        sources[variant] = paths
    require(job["variants"][VARIANTS[0]][ASSEMBLY] == job["variants"][VARIANTS[1]][ASSEMBLY], "both variants need the identical parent")
    require(job["variants"][VARIANTS[0]][PART] != job["variants"][VARIANTS[1]][PART], "child cache intervention is missing")
    return active, control, output, sources


def run_variant(*, job, active, sources, variant, checkpoints):
    active.mkdir(parents=True, exist_ok=False)
    for name, source in sources.items():
        copyfile(source, active / name)
        require(digest(active / name) == job["variants"][variant][name], "active comparison copy differs")
    row = {"variant": variant}
    entry = {"name": "L1Single"}
    phase = {
        "job": job, "entry": entry, "trial": job["trial"], "lane": variant,
        "folder": active, "reference": job["reference"], "child_path": active / PART,
        "preload": False,
    }
    try:
        edit = measured_phase(parent_path=active / ASSEMBLY, expected=None, save=True, **phase)
        row["edit"] = edit
        if edit["passed"]:
            saved = edit["save"]
            row["reopen"] = measured_phase(parent_path=Path(saved["parent"]), expected=saved, save=False, **phase)
    except Exception as error:
        row["exception"] = repr(error)
    finally:
        checkpoints(row)
        archive = active.parent.parent / "NativeResults" / variant
        archive.parent.mkdir(parents=True, exist_ok=True)
        active.rename(archive)
    return row


def compare_lanes(before, after):
    expected = [before["edit"]["rebuilt"], before["edit"]["edited"], before["reopen"]["rebuilt"]]
    observed = [after["edit"]["rebuilt"], after["edit"]["edited"], after["reopen"]["rebuilt"]]
    return {label: compare_scenes(new, old) for label, new, old in zip(("open_rebuild", "edited", "fresh_reopen"), observed, expected, strict=True)}


def main():
    job_path = Path(sys.argv[1]).resolve(strict=True)
    job = json.loads(job_path.read_bytes())
    require(job["schema"] == "kit.sw2026.prism-partition-native-job.v1", "unexpected native cache comparison job")
    active, control, output, sources = prepare(job, Path(job["checkout_root"]).resolve(strict=True))
    output.mkdir(parents=True, exist_ok=False)
    report_file = output / "Inspection.json"
    report = {
        "schema": "kit.sw2026.prism-partition-native-comparison.v1",
        "started_at": time.time(), "controls": [], "lanes": [], "passed": False,
        "job_sha256": digest(job_path), "tool_sha256": digest(Path(__file__)),
        "heldout_acceptance": False,
    }

    def checkpoint():
        write_json(report_file, report)

    def control_phase(kind):
        row = {"kind": kind}
        report["controls"].append(row)
        inspect(control, result=row, checkpoint=checkpoint)
        row["healthy"] = bool(healthy(row) and row["sha256"] == job["control_sha256"] and row["oracle_identity"]["sha256"] == job["oracle_sha256"])
        checkpoint()
        return row["healthy"]

    def save_lane(row):
        report["lanes"].append(row)
        checkpoint()

    try:
        if control_phase("before"):
            for variant in VARIANTS:
                run_variant(job=job, active=active, sources=sources[variant], variant=variant, checkpoints=save_lane)
    except Exception as error:
        report["exception"] = repr(error)
    finally:
        control_phase("after")
        report["controls_healthy"] = [row.get("healthy") for row in report["controls"]] == [True, True]
        phases = [*report["controls"], *(phase for lane in report["lanes"] for key in ("edit", "reopen") if (phase := lane.get(key)))]
        identities = [row["oracle_identity"]["process_creation_filetime"] for row in phases if row.get("oracle_identity")]
        report["distinct_processes"] = len(set(identities))
        report["inputs_immutable"] = all(digest(path) == job["variants"][variant][name] for variant, paths in sources.items() for name, path in paths.items())
        all_passed = len(report["lanes"]) == 2 and all(
            lane.get("edit", {}).get("passed") and lane.get("reopen", {}).get("passed") for lane in report["lanes"]
        )
        if all_passed:
            report["comparisons"] = compare_lanes(*report["lanes"])
        report["passed"] = bool(
            report["controls_healthy"] and report["inputs_immutable"] and "exception" not in report and
            len(identities) == report["distinct_processes"] == 6 and all_passed and
            all(all(flags.values()) for flags in report["comparisons"].values())
        )
        report["finished_at"] = time.time()
        checkpoint()
    print(json.dumps({"passed": report["passed"], "controls_healthy": report["controls_healthy"], "distinct_processes": report["distinct_processes"]}))
    return int(not report["passed"])


if __name__ == "__main__":
    raise SystemExit(main())
