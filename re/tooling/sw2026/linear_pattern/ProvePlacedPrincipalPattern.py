from argparse import ArgumentParser
from json import loads
from math import isclose
from pathlib import Path
import sys

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))

from ProvePlacedPatternStock import LOCK, pinned, plan
from ProvePrincipalPatternContainer import execute, expect, digest, wire

ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
PHASES = {"original": "pristine-reopen", "pitch": "spacing-reopen", "count": "instances-reopen"}


def neutral_intent(case):
    stock = plan(case)
    sx, sy, _ = stock.seed.bounds_m[0]
    size_x, size_y = case["seed_size_m"]
    axis, plane = (("x", "Right Plane"), ("y", "Top Plane"))[case["direction_component"]]
    expect(case["axis_plane"] == plane, "declared selected plane differs from the independent direction index")
    return {
        "name": "Placed" + stock.name,
        "axis": axis,
        "reverse": case["reverse"],
        "epoch": stock.epoch,
        "plate": stock.plate.bounds_m,
        "seed": stock.seed.bounds_m,
        "count": case["instances"],
        "pitch": case["spacing_m"],
        "count_label": (sx + size_x * 0.5, sy + size_y * 1.5, 0.0),
        "idle_label": (sx + size_x, sy, 0.0),
    }


def measured_case(source, lock, phase, solid):
    phase_name = PHASES[phase]
    selected, = (row for row in lock["phases"] if row["phase"] == phase_name)
    record = loads(pinned(source / lock["name"] / phase_name / "Record.json", selected["record_sha256"]))
    expect(record["passed"] and record["oracle_identity"]["sha256"] == ORACLE
           and record["oracle_identity"]["file_version"] == "34.5.2.0604"
           and record["native_sha256"] == selected["native_sha256"] and record["source_immutable"],
           "requested native comparator does not match its authenticated disclosure")
    reopened = record["reopened"]
    direct = reopened["mass"]
    expect(reopened["bodies"] == solid["body_count"] == 1, "generated and native source body counts differ")
    candidate = (solid["volume_mm3"] * 1e-9, solid["area_mm2"] * 1e-6,
                 *(component * 0.001 for component in solid["centroid_mm"]))
    reference = (direct["volume"], direct["area"], *direct["com"])
    expect(all(isclose(actual, expected, rel_tol=2e-7, abs_tol=1e-14)
               for actual, expected in zip(candidate, reference, strict=True)),
           "generated placed principal shape differs from native-source mass observations")
    return {"record_sha256": selected["record_sha256"], "native_sha256": selected["native_sha256"],
            "body_count": reopened["bodies"], "geometry_values_within_relative_2e_7": len(candidate)}


def main():
    parser = ArgumentParser()
    parser.add_argument("--disclosed", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = args.disclosed
    lock = loads(pinned(source / "SourceLock.json", LOCK))
    expect(lock["cohort"] == "disclosed" and lock["passed"] and lock["control_unchanged"],
           "need the complete disclosed source bracket")
    specs = loads(pinned(source / "FrozenInputs.json", lock["specs_sha256"]))
    compare = {case["name"]: case for case in lock["cases"]}
    generated = {}
    for case in specs["cases"]:
        request = neutral_intent(case)
        variants = {"original": request, "pitch": dict(request, pitch=case["edit_spacing_m"]),
                    "count": dict(request, count=case["edit_instances"])}
        reports = {}
        for phase, local in variants.items():
            report, payload = execute(local)
            if phase == "original":
                expect(execute(local) == (report, payload), "placed archive did not reproduce in a separate worker")
            expect(report["runtime_reads"] == 0 and len(report["streams"]) == 10,
                   "placed candidate needs all ten streams and model-only writes")
            reports[phase] = {"generated": report, "source": measured_case(source, compare[case["name"]], phase, report["solid"])}
        generated[case["name"]] = reports
    expect(len(generated) == 2, "need two independent translated initial models")
    result = {"schema": "kit.sw2026.placed-principal-pattern.v1", "build": "34.5.2.0604",
              "source_lock_sha256": LOCK, "source_spec_sha256": lock["specs_sha256"],
              "model_cases": generated, "fresh_guarded_workers": 8, "complete_model_files": 6,
              "present_streams": 60, "native_source_rows": 6, "native_generated_launches": 0,
              "heldout_cases": 0, "fcstd_credit": 0, "runtime_reads": 0,
              "tool_sha256": digest(HERE.read_bytes())}
    with args.output.open("xb") as handle:
        handle.write(wire(result))
    print({"models": len(generated), "states": 6, "receipt_sha256": digest(args.output.read_bytes())})


if __name__ == "__main__":
    main()
