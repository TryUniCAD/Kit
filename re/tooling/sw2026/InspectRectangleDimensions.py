from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path
from shutil import copyfile

from AuthorCurves import digest, require, write_json


PARAMETERS = ("D1@Sketch1", "D2@Sketch1", "D1@Boss-Extrude1")
ORACLE_FILES = ("InspectFresh.py", "InspectEdit.py", "Author.py", "AuthorCurves.py", "Swapp.py", "OracleIdentity.py")


def checked_file(path, expected, checkout, suffix):
    path = Path(path).resolve(strict=True)
    require(path.is_file() and path.suffix.casefold() == suffix and not path.is_relative_to(checkout), f"invalid staged input {path.name}")
    require(digest(path) == expected, f"SHA-256 mismatch for {path.name}")
    return path


def load_pairs(job, checkout):
    freeze_path = checked_file(job["frozen_receipt"], job["frozen_receipt_sha256"], checkout, ".json")
    freeze = json.loads(freeze_path.read_bytes())
    require(freeze["classification"] == "fresh discovery candidates; vendor acceptance unmeasured", "expected a rectangle discovery freeze")
    staged = Path(freeze["original_path"]).resolve(strict=True)
    require(freeze_path.parent == staged, "candidate directory does not match its authored output path")
    recipe_file = checked_file(staged / "VendorRectangleDiscovery.json", freeze["vendor_authoring_json_sha256"], checkout, ".json")
    recipe = {row["name"]: row for row in json.loads(recipe_file.read_bytes())}
    manifest_path = checked_file(job["source_manifest"], job["source_manifest_sha256"], checkout, ".json")
    manifest = json.loads(manifest_path.read_bytes())
    versions = {record["revision"] for record in manifest["results"]}
    require(versions == {"34.5.2"} and not manifest["dialogs"], "native source authoring has unexpected build or dialogs")
    authored = {record["name"]: record for record in manifest["results"]}
    require(len(authored) == len(manifest["results"]) == len(recipe) == len(freeze["cases"]) == 2, "expected two independently authored rectangle sizes")
    pairs = []
    for entry in freeze["cases"]:
        source_name = Path(entry["source"]).stem
        record = authored[source_name]
        require(record["spec"] == recipe[source_name] and record.get("save") == [True, 0, 0] and "error" not in record, f"native authoring failed for {source_name}")
        source = checked_file(record["path"], record["sha256"], checkout, ".sldprt")
        require(source.name == entry["source"] and source.parent == manifest_path.parent, "source did not come from its recorded authoring directory")
        generated = checked_file(staged / entry["candidate"], entry["generated_sha256"], checkout, ".sldprt")
        require(generated.parent == staged and generated.name == entry["candidate"], "generated candidate path differs from its frozen entry")
        require(source != generated and record["sha256"] != entry["generated_sha256"], "source and generated candidates must have independent bytes")
        require(set(entry["dimensions_m"]) == set(PARAMETERS), "unexpected rectangle parameter names")
        edits = [row for row in entry["edits"] if row["parameter"] in PARAMETERS[:2]]
        require(tuple(row["parameter"] for row in edits) == PARAMETERS[:2], "expected independent width and height edit rows")
        for row in edits:
            target = row["parameter"]
            values = dict(entry["dimensions_m"])
            values[target] = row["value_m"]
            require(values == row["expected_dimensions_m"] and values[target] != entry["dimensions_m"][target], "edit changes the wrong dimensions")
        pairs.append((entry, {"source": (source, record["sha256"]), "generated": (generated, entry["generated_sha256"])}, edits))
    return pairs


def close(actual, expected, *, relative=2e-7, absolute=1e-15):
    return type(actual) in (int, float) and math.isfinite(actual) and math.isclose(actual, expected, rel_tol=relative, abs_tol=absolute)


def distance_values(row, expected):
    actual = row.get("parameters", {})
    return all(close(actual.get(name), value, relative=0, absolute=1e-12) for name, value in expected.items())


def centers_match(actual, expected):
    return isinstance(actual, list) and isinstance(expected, list) and len(actual) == len(expected) == 3 and all(close(a, b) for a, b in zip(actual, expected, strict=True))


def measurement(row, expected, dimensions, *, oracle_sha256, healthy):
    metrics = row.get("mass") or {}
    center = metrics.get("com")
    center_valid = isinstance(center, list) and len(center) == 3
    if center_valid:
        center_valid = all(type(value) in (int, float) and math.isfinite(value) for value in center)
    if expected["com"] is None:
        center_match = center_valid and close(center[2], dimensions["D1@Boss-Extrude1"] / 2)
    else:
        center_match = centers_match(center, expected["com"])
    return {
        "healthy": bool(healthy(row) and row.get("oracle_identity", {}).get("sha256") == oracle_sha256),
        "dimensions_match": distance_values(row, dimensions),
        "body_count_matches": row.get("bodies") == expected["bodies"],
        "mass_properties_match": all(close(metrics.get(key), expected[key]) for key in ("volume", "area", "mass")),
        "center_matches": center_match,
    }


def inspect_edit(*, work, source, expected_sha, request, original_dimensions, inspect, edit, checkpoint, fingerprints):
    work.mkdir(parents=True, exist_ok=False)
    staged = work / source.name
    save = work / (source.stem + "Edited.SLDPRT")
    copyfile(source, staged)
    require(digest(staged) == expected_sha, "editable copy differs from the pinned input")
    target = request["parameter"]
    phase = fingerprints["edit"]
    edit(staged, save, target, request["value_m"], phase, checkpoint, parameter_names=PARAMETERS)
    fingerprints["edited_parameter"] = (
        close(phase.get("original_value_m"), original_dimensions[target], relative=0, absolute=1e-12)
        and close(phase.get("readback_value_m"), request["value_m"], relative=0, absolute=1e-12)
    )
    fingerprints["input_unchanged"] = digest(staged) == expected_sha
    fingerprints["save_healthy"] = bool(
        phase.get("saved") and phase.get("save_errors") == phase.get("save_warnings") == 0
        and save.is_file() and digest(save) == phase.get("edited_copy_sha256")
    )
    if fingerprints["save_healthy"] and not phase.get("exception"):
        inspect(save, result=fingerprints["reopen"], checkpoint=checkpoint, parameter_names=PARAMETERS)
        fingerprints["save_unchanged"] = digest(save) == fingerprints["reopen"].get("sha256") == phase["edited_copy_sha256"]
    checkpoint()


def compare_pair(entry, paths, requests, *, output, oracle_sha256, evidence, phases, inspect, edit, healthy, checkpoint):
    evidence["baseline"] = {}
    evidence["edits"] = []
    for lane, (source, expected_sha) in paths.items():
        row = {"original_sha256": expected_sha}
        evidence["baseline"][lane] = row
        phases.append(row)
        inspect(source, result=row, checkpoint=checkpoint, parameter_names=PARAMETERS)
        row["checks"] = measurement(row, entry["before"], entry["dimensions_m"], oracle_sha256=oracle_sha256, healthy=healthy)
        row["checks"]["source_bound"] = row.get("sha256") == expected_sha and digest(source) == expected_sha
        checkpoint()
    if not all(all(row["checks"].values()) for row in evidence["baseline"].values()):
        return False
    for ordinal, request in enumerate(requests, 1):
        pair = {"parameter": request["parameter"], "value_m": request["value_m"], "lanes": {}}
        evidence["edits"].append(pair)
        for lane, (source, expected_sha) in paths.items():
            row = {"edit": {}, "reopen": {}}
            pair["lanes"][lane] = row
            phases.extend((row["edit"], row["reopen"]))
            inspect_edit(
                work=output / Path(entry["candidate"]).stem / f"Edit{ordinal}" / lane,
                source=source, expected_sha=expected_sha, request=request, original_dimensions=entry["dimensions_m"],
                inspect=inspect, edit=edit, checkpoint=checkpoint, fingerprints=row,
            )
            for kind in ("edit", "reopen"):
                row[kind]["checks"] = measurement(row[kind], request["expected_after"], request["expected_dimensions_m"], oracle_sha256=oracle_sha256, healthy=healthy)
            row["center_survives_save"] = centers_match((row["reopen"].get("mass") or {}).get("com"), (row["edit"].get("mass") or {}).get("com"))
        source, generated = (pair["lanes"][lane] for lane in ("source", "generated"))
        pair["center_matches"] = {
            kind: centers_match((generated[kind].get("mass") or {}).get("com"), (source[kind].get("mass") or {}).get("com"))
            for kind in ("edit", "reopen")
        }
        pair["passed"] = all(pair["center_matches"].values()) and all(
            row.get("save_healthy") and row.get("save_unchanged") and row["edited_parameter"] and row["input_unchanged"]
            and row["center_survives_save"]
            and all(all(row[kind]["checks"].values()) for kind in ("edit", "reopen"))
            for row in pair["lanes"].values()
        )
        checkpoint()
    return all(pair["passed"] for pair in evidence["edits"])


def main():
    from InspectEdit import edit
    from InspectFresh import healthy, inspect

    job_path = Path(sys.argv[1]).resolve(strict=True)
    job = json.loads(job_path.read_bytes())
    require(job["schema"] == "kit.sw2026.rectangle-native-discovery-job.v1", "unexpected rectangle native discovery job")
    checkout = Path(job["checkout_root"]).resolve(strict=True)
    output = Path(job["output"]).resolve()
    require(not output.is_relative_to(checkout), "native discovery receipts must stay outside the checkout")
    control = checked_file(job["control"], job["control_sha256"], checkout, ".sldprt")
    pairs = load_pairs(job, checkout)
    immutable = [(control, job["control_sha256"]), *((path, value) for _, lanes, _ in pairs for path, value in lanes.values())]
    require(len({path for path, _ in immutable}) == len(immutable), "control and comparison documents must be separate files")
    output.mkdir(parents=True, exist_ok=False)
    report_path = output / "RectangleInspection.json"
    report = {
        "schema": "kit.sw2026.rectangle-native-discovery.v1",
        "job_sha256": digest(job_path),
        "frozen_receipt_sha256": job["frozen_receipt_sha256"],
        "source_manifest_sha256": job["source_manifest_sha256"],
        "tool_sha256": {name: digest(Path(__file__).with_name(name)) for name in (*ORACLE_FILES, Path(__file__).name)},
        "oracle_sha256": job["oracle_sha256"],
        "started_at": time.time(), "controls": [], "pairs": [], "passed": False, "heldout_acceptance": False,
    }
    phases = []

    def checkpoint():
        write_json(report_path, report)

    def control_phase(kind):
        row = {"kind": kind}
        report["controls"].append(row)
        phases.append(row)
        inspect(control, result=row, checkpoint=checkpoint)
        row["healthy"] = bool(healthy(row) and row.get("sha256") == job["control_sha256"] and row.get("oracle_identity", {}).get("sha256") == job["oracle_sha256"])
        checkpoint()
        return row["healthy"]

    try:
        if control_phase("before"):
            for entry, paths, edits in pairs:
                evidence = {"candidate": entry["candidate"], "source": entry["source"]}
                report["pairs"].append(evidence)
                evidence["passed"] = compare_pair(
                    entry, paths, edits, output=output, oracle_sha256=job["oracle_sha256"],
                    evidence=evidence, phases=phases, inspect=inspect, edit=edit, healthy=healthy, checkpoint=checkpoint,
                )
                checkpoint()
    except Exception as error:
        report["exception"] = repr(error)
    finally:
        try:
            control_phase("after")
        except Exception as error:
            report["control_after_exception"] = repr(error)
        report["sources_unchanged"] = all(path.is_file() and digest(path) == value for path, value in immutable)
        report["controls_healthy"] = [row.get("healthy") for row in report["controls"]] == [True, True]
        identities = [row.get("oracle_identity", {}).get("process_creation_filetime") for row in phases]
        report["expected_processes"] = 2 + sum(2 + 4 * len(edits) for _, _, edits in pairs)
        report["fresh_processes"] = len(set(value for value in identities if type(value) is int and value > 0))
        report["passed"] = bool(
            report["controls_healthy"] and report["sources_unchanged"] and "exception" not in report
            and len(identities) == report["fresh_processes"] == report["expected_processes"]
            and len(report["pairs"]) == len(pairs) and all(row.get("passed") for row in report["pairs"])
        )
        report["finished_at"] = time.time()
        checkpoint()
    print(json.dumps({"passed": report["passed"], "controls_healthy": report["controls_healthy"], "pairs": len(report["pairs"])}))
    return int(not report["passed"])


if __name__ == "__main__":
    raise SystemExit(main())
