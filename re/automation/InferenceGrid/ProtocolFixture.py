# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ApplicationWorkers"))

from Records import canonical, digest, specification
from InferenceGrid.Evidence import GridInputs, KScopeGap, KScopeSpecPin
from InferenceInputs import sha256
from FusionPhasePlan import CASES, SCOPE, phase_paths

# these synthetic protocol packets exercise consistency without representing native evidence
REVISION = "5018f106b8287c83756233c677cc155e8b963357"
ROOT = Path(__file__).resolve().parents[3]
PATHS = {
    "tool": "re/automation/CaptureTools/ScopeControl/FusionScopeControl.py",
    "model": "re/automation/CaptureTools/ScopeControl/FusionScopeModel.py",
    "specification": "re/automation/PairedCaptures/ScopeControl/ScopeControlSpec.json",
    "fresh_process": "re/automation/PairedCaptures/FusionFreshProcess.py",
    "helper": "re/automation/PairedCaptures/FusionCapture.py",
    "bindings": "re/automation/PairedCaptures/FusionBindings.py",
    "control": "re/Fusion/Study/thinextrudes-c1632bcb5efe/ordinary_rectangle_control.f3d",
}


# sealed protocol inputs must use the actual source bytes rather than invented source identities
def source_pins():
    pins = {}
    for role, path in PATHS.items():
        raw = subprocess.check_output(["git", "show", f"{REVISION}:{path}"], cwd=ROOT)
        pins[role] = {"path": path, "sha256": sha256(raw), "size_bytes": len(raw)}
    return pins


# analytic boxes isolate archive custody from any cad parser or application behavior
def body(identity, cut):
    lower, upper = (
        ([0, 0, 0], [40, 20, 10]) if identity == "A" else ([10, 5, -10], [30, 15, -5])
    )
    return {
        "bounds_mm": [lower, upper],
        "centroid_mm": [20, 10, 5 if identity == "A" else -7.5],
        "volume_mm3": (
            (7200 if cut else 8000) if identity == "A" else (600 if cut else 1000)
        ),
        "face_count": 10 if cut else 6,
        "edge_count": 24 if cut else 12,
        "vertex_count": 16 if cut else 8,
        "producer": {
            "name": "ScopeBoss" + identity,
            "native_id": 1 if identity == "A" else 3,
            "identity_kind": "fusion_timeline_index",
        },
    }


# all three analytic cases retain the deliberately unobserved saved policy
def scope_case(mode, archive):
    targets = ["A"] if mode == "explicit_a" else ["A", "B"]
    intact = {"bodies": {identity: body(identity, False) for identity in ("A", "B")}}
    stage = {
        "bodies": {
            identity: body(identity, identity in targets) for identity in ("A", "B")
        },
        "cut": {
            "status": "verified",
            "depth_mm": None,
            "end_condition": "through_all",
            "direction_world": [0, 0, -1],
            "target_body_ids": targets,
            "observed_policy": None,
            "native": {
                "operation": 1,
                "extent_type": "adsk::fusion::ThroughAllExtentDefinition",
                "start_type": "adsk::fusion::ProfilePlaneStartDefinition",
                "is_positive_direction": False,
                "has_two_extents": False,
                "participant_marker": 5,
                "participant_count": len(targets),
                "support_cap": {
                    "status": "verified",
                    "marker": 4,
                    "boss_start_face_matches": 0,
                    "boss_end_face_matches": 1,
                    "boss_body_matches": 1,
                    "normal_world": [0, 0, 1],
                    "signed_offset_mm": 10,
                },
            },
        },
    }
    return {
        "mode": mode,
        "archive": archive,
        "authoring_participant_assignment": None if mode == "automatic" else targets,
        "fresh_import": {
            "source_bytes_verified_after_readback": True,
            "compute_all_return": True,
        },
        "before_cut": intact,
        "before_save": deepcopy(stage),
        "after_reopen": {**deepcopy(stage), "before_cut": deepcopy(intact)},
        "after_rebuild": {**deepcopy(stage), "before_cut": deepcopy(intact)},
    }


# each mutation is resealed so only its intended cross record inconsistency remains
def phase_packet(queue, plan, phase, previous, variant):
    birth = 1704067200 if phase == "a" else 1704067300
    host = {
        "pid": 427 if phase == "a" else 428,
        "started": datetime.fromtimestamp(birth, timezone.utc).strftime(
            "%a %b %d %H:%M:%S %Y"
        ),
    }
    if variant.startswith("windows-"):
        ticks = (birth + 11644473600) * 10000000
        host["started"] = f"windows:{ticks}"
    process = {"pid": host["pid"], "start_unix_seconds": birth}
    if variant.startswith("windows-"):
        process["started"] = host["started"]
    files = {}
    cases = []
    for mode in CASES:
        raw = f"authored protocol fixture only:{mode}".encode()
        if variant == "archive-substitution" and phase == "b" and mode == "automatic":
            raw += b":substituted"
        path = f"fusion-{mode}.f3d"
        files[f"phase-{phase}.{mode}"] = raw
        cases.append(
            scope_case(
                mode, {"file": path, "sha256": sha256(raw), "size_bytes": len(raw)}
            )
        )
    report = {
        "schema": 1,
        "scope": SCOPE,
        "application": "fusion",
        "application_build": "1.2.3",
        "source_revision": REVISION,
        "pins": plan["pins"],
        "specification_sha256": KScopeSpecPin,
        "phase": phase,
        "status": "complete",
        "errors": [],
        "plan_sha256": queue["plan_sha256"],
        "cases": cases,
        "process": process,
        "started_unix_seconds": birth + 1,
        "ended_unix_seconds": birth + 10,
        "healthy_control_before": {
            "compute_all_return": True,
            "native_input": plan["pins"]["control"],
        },
        "healthy_control_after": {
            "compute_all_return": True,
            "native_input": plan["pins"]["control"],
        },
        "previous_process": None if previous is None else previous[0]["process"],
        "previous_phase_report_sha256": None if previous is None else previous[1],
    }
    if phase == "b":
        native = cases[0]["before_save"]["cut"]["native"]
        if variant == "raw-positive":
            for row in cases:
                for stage in ("before_save", "after_reopen", "after_rebuild"):
                    row[stage]["cut"]["native"]["is_positive_direction"] = True
        elif variant == "flag-integer":
            native["is_positive_direction"] = 1
        elif variant == "support-late":
            native["support_cap"]["marker"] = native["participant_marker"]
        elif variant == "support-boolean":
            native["support_cap"]["marker"] = True
        elif variant == "support-normal":
            native["support_cap"]["normal_world"] = [0, 0, -1]
        elif variant == "support-offset":
            native["support_cap"]["signed_offset_mm"] = 0
        elif variant == "no-removal":
            cases[0]["before_save"]["bodies"]["A"] = body("A", False)
    if phase == "a" and variant.startswith("start-"):
        field = variant.removeprefix("start-")
        if field == "missing":
            del report["started_unix_seconds"]
        else:
            report["started_unix_seconds"] = {
                "null": None,
                "boolean": True,
                "early": birth - 1,
                "late": birth + 11,
            }[field]
    if variant == "birth-substitution":
        process["start_unix_seconds"] -= 1
    if variant == "windows-birth" and phase == "b":
        process["started"] = f"windows:{ticks + 1}"
    if phase == "a" and variant == "reversed-time":
        report["ended_unix_seconds"] = birth - 1
    if phase == "a" and variant == "future-time":
        report["ended_unix_seconds"] = 999999999999
    if phase == "a" and variant == "boolean-time":
        report["ended_unix_seconds"] = True
    if phase == "b" and variant == "one-body":
        del cases[0]["before_cut"]["bodies"]["B"]
    if phase == "b" and variant == "invented-policy":
        cases[0]["before_save"]["cut"]["observed_policy"] = "automatic"
    if phase == "a" and variant == "unhealthy-control":
        report["healthy_control_after"]["compute_all_return"] = False
    if phase == "a" and variant == "fixture-marker":
        report["fixture_only"] = True
    raw_report = canonical(report).encode()
    receipt = {
        "schema": 1,
        "scope": SCOPE,
        "phase": phase,
        "status": "complete",
        "plan_sha256": queue["plan_sha256"],
        "report_sha256": sha256(raw_report),
    }
    files[f"phase-{phase}.report"] = raw_report
    files[f"phase-{phase}.receipt"] = canonical(receipt).encode()
    handoff = (
        {
            "installation": queue["installation"],
            "job_id": "a" * 32,
            "reason": "restart_required",
            "host": host,
            "plan_sha256": queue["plan_sha256"],
            "at": birth + 11,
            "owner": "external_application_owner",
        }
        if phase == "a"
        else None
    )
    if phase == "a":
        if variant == "missing-handoff":
            handoff = None
        elif variant.startswith("handoff-") and variant != "handoff-record":
            field = variant.removeprefix("handoff-")
            handoff[field] = {"job_id": "malformed", "at": birth + 9}.get(
                field, "wrong"
            )
    elif variant == "unexpected-handoff":
        handoff = {"fixture": "unexpected phase b fence"}
    proof = {
        "claim": "unqualified_application_observation",
        "phase": phase,
        "scope": SCOPE,
        "plan_sha256": queue["plan_sha256"],
        "host": host,
        "fusion_version": "1.2.3",
        "restart_handoff": handoff,
    }
    dispatch = {
        "version": 1,
        "provider": "autodesk.fusion.addin",
        "status": "completed",
        "source_revision": REVISION,
        "installation": queue["installation"],
        "host": host,
        "finished_at": birth + 12,
        "proof": proof,
        "files": {
            role: {
                "path": path,
                "sha256": sha256(files[role]),
                "size_bytes": len(files[role]),
            }
            for role, path in phase_paths(queue, phase).items()
        },
    }
    files["dispatch"] = canonical(dispatch).encode()
    manifest = {
        role: {"sha256": sha256(raw), "size_bytes": len(raw)}
        for role, raw in files.items()
    }
    records = {
        "application": "fusion",
        "phase": phase,
        "scope": SCOPE,
        "installation": queue["installation"],
        "plan_sha256": queue["plan_sha256"],
        "native_qualified": False,
        "host": host,
        "fusion_version": "1.2.3",
        "restart_handoff": handoff,
    }
    if phase == "a" and variant == "handoff-record":
        records["restart_handoff"] = None
    accepted = {
        "session_version": 1,
        "output_artifacts_version": 1,
        "receipt": {
            "receipt_version": 1,
            "job_id": queue["jobs"][phase],
            "orphan": False,
            "stop_reason": None,
            "exit_status": 0,
            "signal": None,
        },
        "result": {"outcome": "completed", "records": records, "artifacts": manifest},
        "output_artifacts": manifest,
    }
    return report, sha256(raw_report), files, canonical(accepted).encode()


# authored snapshots bind every altered artifact through the real inference command boundary
def write_fixture(folder, variant):
    folder.mkdir(exist_ok=True)
    (folder / "inputs").mkdir()
    plan = {
        "schema": 1,
        "scope": SCOPE,
        "source_revision": REVISION,
        "pins": source_pins(),
    }
    queue = {
        "scope": SCOPE,
        "cases": list(CASES),
        "source_revision": REVISION,
        "installation": "fusion:protocol",
        "resource": "application:protocol",
        "jobs": {
            phase: "fusion-phase:" + "f" * 64 + ":" + phase for phase in ("a", "b")
        },
        "plan_sha256": digest(plan),
        "plan_binding": "fusion-plan:" + digest(plan),
    }
    report = {
        "inference_version": 1,
        "scope": KScopeGap,
        "status": "needs-distinguishing-evidence",
        "affected_archives": {
            sha256(b"authored fusion"): "fusion.f3d",
            sha256(b"authored sw"): "solidworks.sldprt",
        },
        "requested_grid": {
            "specification": PATHS["specification"],
            "sha256": KScopeSpecPin,
        },
    }
    job_id = "inference:" + digest(KScopeGap)
    origin = {"inputs": {"plan": {"binding": "authored:gap", "sha256": digest(report)}}}
    previous = {
        "receipt_version": 1,
        "outcome": "waiting_evidence",
        "job_id": job_id,
        "generation": 1,
        "snapshot": origin,
        "fingerprint": digest(origin),
    }
    previous_pin = digest(previous)
    selectors = {"plan": "authored:gap", **GridInputs(queue, previous_pin)}
    raw_inputs = {
        "plan": canonical(report).encode(),
        "grid-queue": canonical(queue).encode(),
        "grid-plan": canonical(plan).encode(),
        "grid-previous": canonical(previous).encode(),
    }
    prior = None
    dependencies = {}
    for phase in ("a", "b"):
        observed, report_pin, files, accepted = phase_packet(
            queue, plan, phase, prior, variant
        )
        raw_inputs[f"phase-{phase}.accepted"] = accepted
        raw_inputs[f"phase-{phase}.dispatch"] = files["dispatch"]
        for role in selectors:
            if role in files:
                raw_inputs[role] = files[role]
        dependencies[queue["jobs"][phase]] = {
            "receipt": sha256(f"authored {phase} receipt".encode()),
            "result": sha256(accepted),
        }
        prior = observed, report_pin
    inputs = {}
    for role, raw in raw_inputs.items():
        pin = sha256(raw)
        (folder / "inputs" / pin).write_bytes(raw)
        inputs[role] = {
            "binding": selectors[role],
            "sha256": pin,
            "path": "inputs/" + pin,
        }
    job = specification(
        {
            "id": job_id,
            "kind": "inference.paired-gap",
            "inputs": selectors,
            "depends_on": sorted(dependencies),
            "resources": [],
            "rule_version": "protocol@1",
            "tool_version": REVISION,
            "options": {"scope": KScopeGap, "grid_from_receipt": previous_pin},
        }
    )
    snapshot = {
        "definition_hash": digest(job),
        "dependencies": dependencies,
        "inputs": {
            role: {key: item[key] for key in ("binding", "sha256")}
            for role, item in inputs.items()
        },
    }
    packet = {
        "session_version": 1,
        "generation": 2,
        "job": job,
        "inputs": inputs,
        "dependencies": dependencies,
        "fingerprint": digest(snapshot),
        "work": "work",
        "result": "result.json",
    }
    (folder / "job.json").write_text(canonical(packet))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Author synthetic inference protocol controls without native CAD evidence"
    )
    parser.add_argument("folder", type=Path)
    parser.add_argument("variant")
    args = parser.parse_args()
    write_fixture(args.folder, args.variant)
