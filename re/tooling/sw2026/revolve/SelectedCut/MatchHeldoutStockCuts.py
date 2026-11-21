from math import isfinite
from pathlib import Path
import json
import sys

from EvaluateHeldoutStockCuts import LOCK, LOCK_SHA, ORIGINALS, SCHEMA, checked, digest, encode, publish, require
from RunScopedRevolveNative import ORACLE_SHA, path_for, source_lock, validate_specs

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "EndModes"))

from ProveSelectedRevCut import dispatch


def native_receipt(path, pin):
    value = json.loads(checked(path, pin))
    require(value["passed"] and value["oracle_identity"]["sha256"] == ORACLE_SHA,
            "a locked native observation failed or used a different build")
    return value


def source_states(case, source):
    folder = Path(ORIGINALS) / case["name"]
    name = case["name"]
    rows = {phase["phase"]: phase for phase in source["phases"]}
    require(set(rows) == {"author", "reopen", "edited-reopen"} and all(row["passed"] for row in rows.values()),
            "source lacks the measured author, edit or reopen phase")
    initials = native_receipt(folder / f"{name}.reopen.json", rows["reopen"]["sha256"])
    edited = native_receipt(folder / f"{name}-edited.edited-reopen.json", rows["edited-reopen"]["sha256"])
    saved = initials["edited_derivative"]
    require(initials["source_immutable"] and initials["edit"]["passed"] and saved["save_status"] == [True, 0, 0],
            "the pre-writer edit or save did not finish cleanly")
    original, derivative = folder / path_for(case), folder / path_for(case, "-edited")
    checked(original, source["native_sha256"])
    checked(derivative, saved["sha256"])
    return originals(initials, edited), ((original, source["native_sha256"]), (derivative, saved["sha256"]))


def originals(first, last):
    return first["reopened"], first["edited"], last["reopened"]


def measured_equal(first, second, tolerance):
    return (isfinite(first) and isfinite(second)
            and (format(first, ".6g") == format(second, ".6g") or abs(first - second) <= tolerance))


def contrast(source, candidate):
    checks = {
        "ordered_tree": source["features"] == candidate["features"],
        "cut_parents": source["parents"] == candidate["parents"],
        "feature_type": source["feature_type"] == candidate["feature_type"],
        "body_count": source["body_count"] == candidate["body_count"] == 2,
        "stock_selection": source["definition"]["scope"] == candidate["definition"]["scope"],
        "angular_driver": (
            source["drivers"]["angle"]["name"] == candidate["drivers"]["angle"]["name"]
            and source["drivers"]["angle"]["editable"] and candidate["drivers"]["angle"]["editable"]
            and measured_equal(source["drivers"]["angle"]["value"], candidate["drivers"]["angle"]["value"], 1e-13)
        ),
        "axis_geometry": (
            source["definition"]["axis"]["name"] == candidate["definition"]["axis"]["name"]
            and all(measured_equal(left, right, 1e-12)
                    for a, b in zip(source["definition"]["axis"]["points"], candidate["definition"]["axis"]["points"], strict=True)
                    for left, right in zip(a, b, strict=True))
        ),
    }
    source_bodies, target_bodies = source["measured"], candidate["measured"]
    checks["body_names"] = source_bodies.keys() == target_bodies.keys() and all(
        target_bodies[name]["name"] == body["name"] for name, body in source_bodies.items()
    )
    checks["body_topology"] = checks["body_names"] and all(
        all(body[key] == target_bodies[name][key] for key in ("faces", "edges", "vertices"))
        for name, body in source_bodies.items()
    )
    for measure, tolerance in (("volume_m3", 1e-16), ("area_m2", 1e-14), ("com_m", 1e-12)):
        checks[measure] = checks["body_names"] and all(
            (all(measured_equal(left, right, tolerance)
                 for left, right in zip(body[measure], target_bodies[name][measure], strict=True))
             if measure == "com_m" else measured_equal(body[measure], target_bodies[name][measure], tolerance))
            for name, body in source_bodies.items()
        )
    return checks


def compare(private, source, manifest, generation, native_pin):
    packet = private / "CandidatePacket"
    native = json.loads(checked(packet / "Inspection/Result.json", native_pin))
    custody = source_lock(checked(source / LOCK, LOCK_SHA))
    cases = validate_specs(json.loads(checked(packet / "ModelSpecs.json", custody["spec_sha256"])))
    require(native["packet_sha256"] == digest((packet / "Packet.json").read_bytes())
            and native["codec_revision"] == manifest["writer_revision"]
            and native["oracle_sha256"] == ORACLE_SHA and native["passed"]
            and native["distinct_processes"] == 6 and native["idle_after"] and native["controls_healthy"],
            "held-out evaluation lacks a complete controlled native candidate lifecycle")
    for role in ("before", "after"):
        control = json.loads(checked(packet / "Inspection" / f"Control{role.title()}.json",
                                    native[role]["sha256"]))
        require(native[role]["passed"] and control["oracle_identity"]["sha256"] == ORACLE_SHA,
                "held-out candidate control used a different build or failed")

    comparison = {}
    for case, locked in zip(cases, custody["sources"], strict=True):
        name = case["name"]
        row = native["cases"][name]
        loc = packet / "Inspection" / name
        initial, last = (native_receipt(loc / filename, phase["sha256"])
                         for filename, phase in zip(("Initial.json", "FreshReopen.json"), row["phases"], strict=True))
        source_phases, source_parts = source_states(case, locked)
        target_phases = originals(initial, last)
        candidate_pin = row["candidate_sha256"]
        require(candidate_pin == generation["construction"][name]["sha256"] == generation["files"][f"Candidates/{path_for(case)}"],
                "a held-out candidate lost its pre-open generation identity")
        checked(packet / "Candidates" / path_for(case), candidate_pin)
        checks = [contrast(a, b) for a, b in zip(source_phases, target_phases, strict=True)]
        saved = dispatch(loc / "Saved.SLDPRT", row["saved_sha256"], observed=last)
        original, source_digest = source_parts[0]
        locked_final, locked_final_digest = source_parts[1]
        original_sdk = dispatch(original, source_digest, observed={
            "reopened": source_phases[0], "job": {"case": case},
        })
        edited_sdk = dispatch(locked_final, locked_final_digest, observed={
            "reopened": source_phases[2], "job": {"case": dict(case, angle_deg=case["edit_angle_deg"])},
        })
        sdk = (original_sdk, edited_sdk, saved)
        require(all(value["unexpected_runtime_reads"] == 0 and len(value["exact_streams"]) == 2 for value in sdk),
                "source or candidate SDK projection used an external file or lost a linked stream")
        comparison[locked["case"]] = {
            "source_sha256": source_digest, "source_edited_sha256": locked_final_digest,
            "candidate_sha256": candidate_pin, "candidate_edited_sha256": row["saved_sha256"],
            "source_comparison_checks": checks, "strict_saved_reads": len(sdk),
            "exact_linked_streams": sum(len(value["exact_streams"]) for value in sdk),
            "passed": all(all(state.values()) for state in checks),
        }
    result = {
        "schema": SCHEMA, "source_lock_sha256": LOCK_SHA, "native_result_sha256": native_pin,
        "writer_revision": manifest["writer_revision"], "writer_source_tree": manifest["writer_source_tree"],
        "oracle_build": "34.5.2.0604", "oracle_sha256": ORACLE_SHA,
        "native_processes": native["distinct_processes"], "control_brackets_healthy": True,
        "original_native_files_read_by_generation": generation["original_native_files_read_by_generation"],
        "runtime_reads": generation["runtime_reads"], "public_writer": False,
        "passed": all(row["passed"] for row in comparison.values()), "cases": comparison,
    }
    pin = publish(private / "Comparison.json", encode(result))
    return {"comparison_sha256": pin, "passed": result["passed"],
            "passed_cases": sum(row["passed"] for row in comparison.values())}
