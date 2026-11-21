from __future__ import annotations

import argparse
import json
from pathlib import Path
from uuid import UUID

from CheckDrawingDefinitions import DISCLOSED, SOURCE_LOCK, checked_artifacts, digest, require
from Classes import registry
from Core import Load, Obj, Store
from Dsl import obj
from defs.Definition import load_definition
from convert.adapters.solidworks.Container.Container import SldprtArchive

from builders.DrawingTail import drawing_options, empty_drawing_tail


def inspect_disclosed(*, corpus, case, rules):
    saved, _, _ = checked_artifacts(corpus, case)
    archive = SldprtArchive.from_bytes(saved)
    definition, _ = load_definition(archive.require("Contents/Definition"), rules, 19000)
    model = definition.head["model"]
    layer = model["fed0"]
    blocks = model["fe80"]
    properties = model["f16a8"]
    require(layer["f30"] is model and layer["f08"] is None, "native empty drawing layer owner differs")
    require(layer["n"] == 0 and layer["f38"] == -1 and layer["f20"]["f08"] == {"n": 0, "f18": 0, "data": b""},
            "native empty layer-mask allocation differs")
    require(blocks["blocks"]["f30"] is blocks and blocks["blocks"]["n70"] == blocks["blocks"]["n98"] == 0,
            "native empty block-map owner differs")
    require(UUID(bytes_le=blocks["f380"]).version == 4, "native block manager does not carry a Windows UUID4")
    require(model["f1444"] == drawing_options(auto_dim_text_link=True), "native drawing bit options differ")
    require(properties["f18"] is model, "native drawing property manager lost its backpointer")
    require(model["f14f8"] == {"n": 0, "items": [], "f38": 1}, "unqualified native drawing XML-name map")
    return {
        "name": case["name"], "source_sha256": digest(saved), "drawing_flags": model["f1444"],
        "layer_count": layer["n"], "layer_mask_words": layer["f20"]["f08"]["n"],
        "empty_block_map": True, "block_guid_version": 4, "component_property_count": properties["n10"],
    }


def inspect_constructed(*, option, rules):
    root = Obj("moDrawing_c")
    sheet = Obj("moDrSheet", {"owner": root})
    identity = UUID("51b146ee-6138-4483-96fe-78d27153326f")
    fields = empty_drawing_tail(
        owner=root, active_sheet=sheet, auto_dim_text_link=option, block_identity=identity,
        created_at=1000000000, date_code=2026306, parasolid_version=370108,
    )
    commands = [obj("fe80"), obj("fed0"), *rules.classes["moDrawing_c"][2:]]
    rules.classes["probe.DrawTail"] = commands
    writer = Store(1, rules, 19000)
    writer.bind_direct_objects((root, sheet))
    rules.run_store("probe.DrawTail", writer, fields, root)
    encoded = bytes(writer.out)
    decoded, replay_root, replay_sheet = {}, Obj("moDrawing_c"), Obj("moDrSheet")
    reader = Load(encoded, 1, rules, 19000)
    reader.bind_direct_objects((replay_root, replay_sheet))
    rules.run_load("probe.DrawTail", reader, decoded, replay_root)
    require(reader.left() == 0 and reader.count == writer.count, "generated drawing suffix did not exhaust its fields")
    require(
        decoded["f1430"] is replay_sheet and decoded["fed0"]["f30"] is replay_root
        and decoded["f16a8"]["f18"] is replay_root and decoded["fe80"]["blocks"]["f30"] is decoded["fe80"],
        "generated drawing managers lost archive identities",
    )
    require(UUID(bytes_le=decoded["fe80"]["f380"]) == identity, "generated sketch-block manager identity changed")
    require(decoded["f1444"] == 0x100 + int(option), "generated drawing flag did not follow authored preference")
    return {"auto_dim_text_link": option, "bytes": len(encoded), "sha256": digest(encoded), "map_next_index": reader.count}


def main():
    parser = argparse.ArgumentParser(description="Measure the owner aliases and format rules for an empty SOLIDWORKS drawing tail")
    parser.add_argument("corpus", type=Path)
    args = parser.parse_args()
    lock = SOURCE_LOCK.read_bytes()
    cases = {case["name"]: case for case in json.loads(lock)["cases"] if case["name"] in DISCLOSED}
    result = {
        "schema": "kit.sw2026.drawing-tail-fields.v1", "source_lock_sha256": digest(lock),
        "disclosed": [inspect_disclosed(corpus=args.corpus, case=cases[name], rules=registry()) for name in DISCLOSED],
        "generated_subgraph": [inspect_constructed(option=value, rules=registry()) for value in (False, True)],
        "native_acceptance": False,
    }
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
