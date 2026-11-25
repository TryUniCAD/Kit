# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of the
# PolyForm Strict License 1.0.0 and voids all licenses granted to you
# under it immediately and permanently.

import argparse
from copy import copy
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
from zipfile import ZipFile

from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument

ROLES = {".smbh": "history", ".smb": "snapshot", ".protein": "material"}


def digest(payload):
    return sha256(payload).hexdigest()


def inventory(archive):
    entries = archive.infolist()
    result = {entry.filename: archive.read(entry) for entry in entries}
    if len(result) != len(entries):
        raise ValueError("Duplicate members invalidate the display contrast")
    return result


def pack(entries, comment, parts, replacements):
    stream = BytesIO()
    with ZipFile(stream, "w") as archive:
        archive.comment = comment
        for entry in entries:
            value = replacements.get(entry.filename, parts[entry.filename])
            archive.writestr(copy(entry), value)
    return stream.getvalue()


def normalized_members(source, normalized):
    if source.keys() != normalized.keys():
        raise ValueError("Normalization changes the member inventory")
    changes = {name: normalized[name] for name, value in source.items() if value != normalized[name]}
    expected = {ROLES.get(Path(name).suffix): name for name in changes}
    if set(expected) != set(ROLES.values()) or len(changes) != len(ROLES):
        raise ValueError("Expected one changed history, snapshot and material member")
    return changes, expected


def capture(label, payload, model, source, expected):
    with ZipFile(BytesIO(payload)) as archive:
        actual = inventory(archive)
    if actual.keys() != source.keys():
        raise ValueError(f"{label} changes the source inventory")
    change = {name: digest(value) for name, value in actual.items() if value != source[name]}
    if change != {name: digest(value) for name, value in expected.items()}:
        raise ValueError(f"{label} changes an unexpected member payload")
    if ReadDocument(payload) != model:
        raise ValueError(f"{label} changes the complete typed model")
    return {"role": label, "sha256": digest(payload), "changed_members": change}


def prepare(source, expected_digest):
    if digest(source) != expected_digest:
        raise ValueError("Source archive SHA-256 disagrees with custody")
    model = ReadDocument(source)
    normalized = EmitParsed(model)
    with ZipFile(BytesIO(source)) as archive:
        original = inventory(archive)
        infos, comment = archive.infolist(), archive.comment
    with ZipFile(BytesIO(normalized)) as archive:
        changes, roles = normalized_members(original, inventory(archive))
    variants = [("original", source, {}), ("repacked-control", pack(infos, comment, original, {}), {})]
    for role, name in sorted(roles.items()):
        selected = {name: changes[name]}
        variants.append((f"{role}-only", pack(infos, comment, original, selected), selected))
    variants += [
        ("normalized-members", pack(infos, comment, original, changes), changes),
        ("normalized-archive", normalized, changes),
    ]
    report = [capture(label, payload, model, original, expected) for label, payload, expected in variants]
    if len({row["sha256"] for row in report[1:6]}) != 5:
        raise ValueError("Repacked contrast roles are indistinguishable")
    return variants, report


def main():
    parser = argparse.ArgumentParser(description="Prepare typed one-member display contrast archives for research")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--source-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    variants, report = prepare(args.source.read_bytes(), args.source_sha256)
    args.output.mkdir()
    for label, payload, _ in variants:
        (args.output / (label + ".f3d")).write_bytes(payload)
    with (args.output / "Report.json").open("x", encoding="utf-8", newline="\n") as report_file:
        json.dump({"source_sha256": args.source_sha256, "native_execution": "pending", "typed_model_equal": True, "cases": report}, report_file, indent=2)
        report_file.write("\n")


if __name__ == "__main__":
    main()
