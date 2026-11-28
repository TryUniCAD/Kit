# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of the
# PolyForm Strict License 1.0.0 and voids all licenses granted to you
# under it immediately and permanently.

import argparse
import json
from datetime import datetime
from hashlib import sha256
from math import isclose, prod
from pathlib import Path

from convert import open_document
from convert.adapters.Fusion.Bridge.CheckContract import CheckContract
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from interchange import CadDocument


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_bound(path, digest):
    raw = path.read_bytes()
    require(sha256(raw).hexdigest() == digest, f"Hash differs for {path.name}")
    return raw


def audit(folder, index_digest, request_digest, candidate_digest, producer_digest, sdk_revision):
    index = json.loads(read_bound(folder / "NarrativeReceiptIndex.json", index_digest))
    batch = json.loads(read_bound(folder / "Batch.json", index["batch_sha256"]))
    pins = {"request_sha256": request_digest, "candidate_sha256": candidate_digest,
            "producer_sha256": producer_digest, "sdk_revision": sdk_revision}
    require(all(index[key] == batch[key] == value for key, value in pins.items()), "Independent pins disagree")
    require(index["runner_sha256"] == batch["runner_sha256"], "Runner binding differs")
    require(index["helpers"] == {role: entry["sha256"] for role, entry in batch["helpers"].items()}, "Helper pins differ")
    for role, entry in batch["helpers"].items():
        read_bound(Path(entry["path"]), index["helpers"][role])
    request_path = Path(batch["request"])
    candidate_path = Path(batch["candidate"])
    request = json.loads(read_bound(request_path, request_digest))
    read_bound(candidate_path, candidate_digest)
    require(request_path.parent == candidate_path.parent, "Staged request and candidate custody differs")
    stage_roles = ("ControlBefore", "Candidate", "Reopen", "ControlAfter")
    require(tuple(stage["stage"] for stage in index["stages"]) == stage_roles, "Fresh stage order differs")
    stages = {}
    previous_end = None
    original_volume = prod(request["dimensions_mm"].values()) / 1000
    for stage in index["stages"]:
        role = stage["stage"]
        raw = json.loads(read_bound(folder / f"{role}.json", stage["receipt_sha256"]))
        require(raw["status"] == "passed", f"Stage {role} did not pass")
        for key in ("stage", "pid", "fusion_version", "started_utc", "ended_utc", "elapsed_ns", "documents_before", "documents_after", "archives", "presentation_errors"):
            require(raw[key] == stage[key], f"Stage {role} {key} binding differs")
        for key in ("runner_sha256", "batch_sha256", "request_sha256", "candidate_sha256"):
            require(raw[key] == index[key], f"Stage {role} {key} differs")
        require(raw["documents_before"] == raw["documents_after"] == 0, f"Stage {role} leaked documents")
        started = datetime.fromisoformat(raw["started_utc"])
        ended = datetime.fromisoformat(raw["ended_utc"])
        require(ended >= started and (previous_end is None or started > previous_end), "Stage timing overlaps")
        previous_end = ended
        stages[role] = stage
    require(len({stage["pid"] for stage in stages.values()}) == len(stage_roles), "Fresh process identity repeated")
    require(len({stage["fusion_version"] for stage in stages.values()}) == 1, "Fusion version changed")
    before, after = stages["ControlBefore"], stages["ControlAfter"]
    control_digest = before["archives"]["VendorControl.f3d"]
    require(after["archives"]["VendorControl.f3d"] == control_digest, "Controls use different exact bytes")
    read_bound(folder / "VendorControl.f3d", control_digest)
    for stage in (before, stages["Candidate"], after):
        state = stage["states"]["rebuilt"]
        density = request["material"]["density_kg_m3"] / 1e6
        require(isclose(state["volume_cm3"], original_volume, abs_tol=1e-8), "Baseline or control volume differs")
        require(state["material"] == request["material"]["label"] and isclose(state["density_kg_per_cm3"], density, abs_tol=1e-12)
                and isclose(state["mass_kg"], original_volume * density, abs_tol=1e-12), "Material or mass differs")
        require(state["material_bindings"]["rgba8"] == [round(channel * 255) for channel in request["material"]["rgba"]], "Effective RGBA differs")

    require(stages["Candidate"]["archives"]["Candidate.f3d"] == candidate_digest, "Loaded candidate differs")
    for name in ("VendorEdited.f3d", "VendorRestored.f3d"):
        saved = index["strict_sdk_saved_readback"][name]
        require(saved["sha256"] == stages["Candidate"]["archives"][name] == stages["Reopen"]["archives"][name], "Save and reopen digests differ")
        payload = read_bound(folder / name, saved["sha256"])
        neutral = open_document(payload, source_format="f3d")
        model = ReadDocument(payload)
        state = CheckContract(neutral.metadata["fusion.native_state"], "model", 2)
        persisted = read_bound(folder / Path(name).with_suffix(".json"), saved["persisted_json_sha256"])
        restored = CadDocument.from_json(persisted.decode("utf-8"))
        require(state == model and restored == neutral, "Persisted loaded semantics differ")
        require(isclose(neutral.bodies[0].topology.volume, saved["volume_mm3"], abs_tol=1e-8), "Strict volume differs")
    return {"candidate_sha256": candidate_digest, "request_sha256": request_digest,
            "control_sha256": control_digest, "index_sha256": index_digest,
            "fusion_version": before["fusion_version"], "distinct_processes": len(stages),
            "stage_seconds": {role: stage["elapsed_ns"] / 1e9 for role, stage in stages.items()},
            "control_appearance_source": before["states"]["rebuilt"]["material_bindings"]["source_type"],
            "candidate_appearance_source": stages["Candidate"]["states"]["rebuilt"]["material_bindings"]["source_type"],
            "presentation_qualified": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audit retained Fusion holdout receipts without starting Fusion")
    parser.add_argument("folder", type=Path)
    for field in ("index_digest", "request_digest", "candidate_digest", "producer_digest", "sdk_revision"):
        parser.add_argument(field)
    args = parser.parse_args()
    print(json.dumps(audit(**vars(args)), sort_keys=True))
