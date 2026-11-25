# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of the
# PolyForm Strict License 1.0.0 and voids all licenses granted to you
# under it immediately and permanently.

import argparse
from collections import Counter
from dataclasses import fields, is_dataclass
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import time
from zipfile import ZipFile

from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.GraphicsCodec.Model.Nodes.BrepWorld import BrepWorld


def digest(payload):
    return sha256(payload).hexdigest()


def inventory(payload):
    with ZipFile(BytesIO(payload)) as archive:
        members = archive.infolist()
        if len(set(archive.namelist())) != len(members):
            raise ValueError("Duplicate archive member")
        return {
            member.filename: {
                "size": member.file_size,
                "method": member.compress_type,
                "sha256": digest(archive.read(member)),
            }
            for member in members
        }


def compare(model_before, model_after):
    sections = Counter()
    loci = Counter()

    def changed(section, owner):
        sections[section] += 1
        loci[f"{section}/{owner}"] += 1

    def walk(left, right, section, owner):
        if type(left) is not type(right):
            changed(section, owner)
        elif left == right:
            return
        elif is_dataclass(left):
            for field in fields(left):
                walk(
                    getattr(left, field.name), getattr(right, field.name),
                    section, f"{type(left).__name__}.{field.name}",
                )
        elif isinstance(left, dict):
            if left.keys() != right.keys():
                changed(section, owner)
            for name in left.keys() & right.keys():
                walk(left[name], right[name], section, f"{owner}.{name}")
        elif isinstance(left, tuple):
            if len(left) != len(right):
                changed(section, owner)
            for a, b in zip(left, right):
                walk(a, b, section, owner)
        else:
            changed(section, owner)

    for field in fields(model_before):
        walk(
            getattr(model_before, field.name), getattr(model_after, field.name),
            field.name, field.name,
        )
    return {"section_differences": dict(sections), "field_differences": dict(sorted(loci.items()))}


def worlds(value):
    if isinstance(value, BrepWorld):
        yield value
    if isinstance(value, tuple):
        for row in value:
            yield from worlds(row)
    if is_dataclass(value):
        for field in fields(value):
            yield from worlds(getattr(value, field.name))


def spatial_state(model):
    history = model.Bodies[0].History if len(model.Bodies) == 1 else None
    return {
        "history_height_mm": getattr(getattr(history, "Model", None), "Height", None),
        "graphics_bounds": [
            {
                "box_cm": world.ModelBox,
                "edges": len(world.EdgeNodes),
                "faces": len(world.FaceNodes),
            }
            for world in worlds(model.Graphics)
        ],
    }


def inspect(path):
    started = time.monotonic()
    original = path.read_bytes()
    model = ReadDocument(original)
    emitted = EmitParsed(model)
    if ReadDocument(emitted) != model:
        raise ValueError(f"{path.name} changes its complete typed model on re-emission")
    before, after = inventory(original), inventory(emitted)
    shared = before.keys() & after.keys()
    comparison = {
        "source_sha256": digest(original),
        "emitted_sha256": digest(emitted),
        "archive_byte_equal": original == emitted,
        "decoded_model_equal": True,
        "spatial_state": spatial_state(model),
        "source_members": before,
        "members_added": sorted(after.keys() - before.keys()),
        "members_removed": sorted(before.keys() - after.keys()),
        "member_payloads_changed": sorted(name for name in shared
                                           if before[name]["sha256"] != after[name]["sha256"]),
        "seconds": round(time.monotonic() - started, 3),
    }
    return comparison, model


def main():
    parser = argparse.ArgumentParser(description="Measure same-source typed re-emission and saved-model differences")
    parser.add_argument("--group", nargs=3, metavar=("BEFORE", "EDITED", "RESTORED"), action="append", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    groups = []
    for before, edited, restored in args.group:
        inventories = {}
        models = {}
        for role, path in (("before", before), ("edited", edited), ("restored", restored)):
            inventories[role], models[role] = inspect(path)
        groups.append({
            "group": edited.parent.name,
            "re_emission": inventories,
            "before_to_restored": compare(models["before"], models["restored"]),
            "edited_to_restored": compare(models["edited"], models["restored"]),
        })
    with args.report.open("x", encoding="utf-8", newline="\n") as report:
        json.dump({"groups": groups}, report, indent=2)
        report.write("\n")


if __name__ == "__main__":
    main()
