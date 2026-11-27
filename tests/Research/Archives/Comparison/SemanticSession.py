# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256 as DigestBytes
from json import dumps as EncodeJson
from pathlib import Path as FilePath

from interchange.serialization.JsonCodec import DumpJson
from tests.Research.Archives.Comparison.SemanticComparisonTests import KTolerances
from tests.Research.Archives.Comparison.SemanticDocuments import MakeDocument
from tests.Research.Inference.InferenceBoundaryTests import WriteInput


# authored protocol contradictions must remain independently sealed before the actual worker evaluates their custody
def PrepareSession(RootPath: FilePath, CaseName: str) -> None:
    Content = DumpJson(MakeDocument()).encode()
    Inputs: dict[str, dict[str, object]] = {
        "first": dict(WriteInput(RootPath, "first", Content)),
        "second": dict(WriteInput(RootPath, "second", Content)),
        "tolerances": dict(
            WriteInput(RootPath, "tolerances", EncodeJson(KTolerances).encode())
        ),
    }
    Selector = (
        {"dependency": "authored:reader"}
        if CaseName in {"valid-direct", "mismatched-direct"}
        else {"dependency": "authored:reader", "artifact": "neutral-document"}
    )
    Dependency = {"receipt": "1" * 64, "result": "2" * 64}
    Dependencies = {
        "missing": {},
        "undeclared": {"authored:reader": Dependency, "authored:extra": Dependency},
        "malformed": {"authored:reader": {**Dependency, "receipt": "not-a-pin"}},
        "missing-result": {"authored:reader": {"receipt": "1" * 64}},
        "extra-field": {"authored:reader": {**Dependency, "unrecognized": "3" * 64}},
        "valid-pending": {
            "authored:reader": {**Dependency, "pending_ci_fingerprint": "3" * 64}
        },
        "invalid-pending": {
            "authored:reader": {**Dependency, "pending_ci_fingerprint": "not-a-pin"}
        },
        "valid-direct": {
            "authored:reader": {**Dependency, "result": Inputs["first"]["sha256"]}
        },
    }.get(CaseName, {"authored:reader": Dependency})
    Inputs["first"]["binding"] = Selector
    JobInfo = {
        "id": "semantic:authored-session",
        "kind": "semantic.compare",
        "inputs": {
            RoleName: Descriptor["binding"] for RoleName, Descriptor in Inputs.items()
        },
        "depends_on": ["authored:reader"],
        "resources": [],
        "rule_version": "authored-rule@1",
        "tool_version": "authored-worker@1",
        "options": {
            "scope": "authored-semantic-session",
            "first_geometry_unit": "mm",
            "second_geometry_unit": "mm",
            "max_candidates": 20000,
        },
        "max_attempts": 3,
        "lease_seconds": 60,
        "timeout_seconds": 300,
        "retry_base_seconds": 1,
    }
    Snapshot = {
        "definition_hash": DigestBytes(
            EncodeJson(
                JobInfo, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            ).encode()
        ).hexdigest(),
        "dependencies": Dependencies,
        "inputs": {
            RoleName: {"binding": Descriptor["binding"], "sha256": Descriptor["sha256"]}
            for RoleName, Descriptor in Inputs.items()
        },
    }
    Packet: dict[str, object] = {
        "session_version": 1,
        "job": JobInfo,
        "inputs": Inputs,
        "dependencies": Dependencies,
        "fingerprint": DigestBytes(
            EncodeJson(
                Snapshot, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            ).encode()
        ).hexdigest(),
        "work": "work",
        "result": "result.json",
    }
    if CaseName == "stale-fingerprint":
        Dependency["receipt"] = "4" * 64
    elif CaseName == "nonfinite":
        Packet["untrusted"] = float("nan")
    Content = EncodeJson(Packet).encode()
    if CaseName == "duplicate":
        Content = b'{"fingerprint":"untrusted",' + Content[1:]
    SessionPath = RootPath / "job.json"
    _ = SessionPath.write_bytes(Content)
    if CaseName == "linked":
        TargetPath = RootPath / "Linked.json"
        _ = SessionPath.rename(TargetPath)
        SessionPath.symlink_to(TargetPath)
    (RootPath / "work").mkdir()
