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


# independently authored packets keep process verification separate from the worker validation implementation
def WriteSession(
    RootPath: FilePath,
    KindName: str,
    Scope: str,
    Inputs: dict[str, dict[str, str]],
    Extra: dict[str, str] | None = None,
) -> dict[str, object]:
    JobValue: dict[str, object] = {
        "id": "inference:authored-session",
        "kind": KindName,
        "inputs": {
            RoleName: Descriptor["binding"] for RoleName, Descriptor in Inputs.items()
        },
        "depends_on": [],
        "resources": [],
        "rule_version": "authored-rule@1",
        "tool_version": "authored-worker@1",
        "options": {"scope": Scope, **(Extra or {})},
        "max_attempts": 3,
        "lease_seconds": 60,
        "timeout_seconds": 300,
        "retry_base_seconds": 1,
    }
    Definition = DigestBytes(
        EncodeJson(
            JobValue, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode()
    ).hexdigest()
    Snapshot = {
        "definition_hash": Definition,
        "dependencies": {},
        "inputs": {
            RoleName: {
                "binding": Descriptor["binding"],
                "sha256": Descriptor["sha256"],
            }
            for RoleName, Descriptor in Inputs.items()
        },
    }
    Packet: dict[str, object] = {
        "session_version": 1,
        "job": JobValue,
        "inputs": Inputs,
        "dependencies": {},
        "fingerprint": DigestBytes(
            EncodeJson(
                Snapshot, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            ).encode()
        ).hexdigest(),
        "work": "work",
        "result": "result.json",
    }
    _ = (RootPath / "job.json").write_text(EncodeJson(Packet), encoding="utf-8")
    return Packet
