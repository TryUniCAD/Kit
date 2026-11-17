# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from InferenceInputs import checksum, parse_metadata, read_file
from Records import canonical, digest, specification


def read_session(session):
    packet = parse_metadata(read_file(session / "job.json", 1024 * 1024))
    if (
        type(packet.get("session_version")) is not int
        or packet["session_version"] != 1
        or packet.get("work") != "work"
        or packet.get("result") != "result.json"
    ):
        raise ValueError("unsupported inference session contract")
    job = packet["job"]
    if canonical(specification(job)) != canonical(job):
        raise ValueError("inference session requires its normalized scheduled job")
    inputs = packet["inputs"]
    if not isinstance(inputs, dict) or set(inputs) != set(job["inputs"]):
        raise ValueError("inference input roles differ from the scheduled job")
    for role, descriptor in inputs.items():
        if (
            not isinstance(descriptor, dict)
            or set(descriptor) != {"binding", "sha256", "path"}
            or descriptor["binding"] != job["inputs"][role]
            or descriptor["path"] != f"inputs/{checksum(descriptor['sha256'])}"
        ):
            raise ValueError("inference input differs from its scheduled descriptor")
    dependencies = packet["dependencies"]
    if not isinstance(dependencies, dict) or set(dependencies) != set(
        job["depends_on"]
    ):
        raise ValueError("inference dependencies differ from the scheduled job")
    for dependency in dependencies.values():
        if not isinstance(dependency, dict) or set(dependency) not in (
            {"receipt", "result"},
            {"receipt", "result", "pending_ci_fingerprint"},
        ):
            raise ValueError(
                "inference dependency lacks its controller receipt and result"
            )
        for pin in dependency.values():
            checksum(pin)
    snapshot = {
        "definition_hash": digest(job),
        "dependencies": dependencies,
        "inputs": {
            role: {"binding": descriptor["binding"], "sha256": descriptor["sha256"]}
            for role, descriptor in inputs.items()
        },
    }
    fingerprint = checksum(packet["fingerprint"])
    if digest(snapshot) != fingerprint:
        raise ValueError("inference session differs from the controller fingerprint")
    return packet, {
        "definition_sha256": snapshot["definition_hash"],
        "fingerprint": fingerprint,
        "rule_version": job["rule_version"],
        "tool_version": job["tool_version"],
        "input_sha256": {
            role: descriptor["sha256"] for role, descriptor in inputs.items()
        },
    }
