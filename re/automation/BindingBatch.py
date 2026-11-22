# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path

from Artifacts import ARTIFACT_BYTES
from Records import label, read_record


def bind_batch(ledger, manifest):
    request = read_record(manifest)
    if set(request) != {"bindings"}:
        raise ValueError("binding manifest must contain only bindings")
    entries = request["bindings"]
    if not isinstance(entries, list) or not 1 <= len(entries) <= 256:
        raise ValueError("binding manifest requires 1–256 entries")

    paths = {}
    for entry in entries:
        if (
            not isinstance(entry, dict)
            or set(entry) != {"name", "file"}
            or not isinstance(entry["file"], str)
            or not entry["file"]
            or "\0" in entry["file"]
        ):
            raise ValueError("each binding requires a name and file path")
        name = label(entry["name"])
        if name in paths:
            raise ValueError(f"binding manifest repeats name {name}")
        paths[name] = manifest.parent / Path(entry["file"])

    results = []
    remaining = ARTIFACT_BYTES
    for name, path in paths.items():
        sha256, size = ledger.objects.put_input(path, remaining)
        remaining -= size
        results.append({"name": name, "sha256": sha256})
    for record in results:
        ledger.set_binding(record["name"], record["sha256"])
    ledger.refresh()
    return {"bindings": results}
