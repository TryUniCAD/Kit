from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parents[2]
sys.path[:0] = [str(ROOT / "src"), str(TOOLS / "serial")]

from CheckDrawingDefinitions import digest, require
from Classes import registry
from Core import Store
from InspectBlankDrawingPair import input_path as prior_input, read_packet as read_prior
from InspectBlankDrawingUi import CASES, SCHEMA, TOOL_NAMES, input_path, read_packet
from defs.Definition import load_definition
from convert.adapters.solidworks.Container.Container import EmitSldprt, SldprtArchive, TemplateFields


DEFINITION = "Contents/Definition"


def values(head):
    return {
        "viewport": bool(head["model"]["f1430"]["has_f430"]),
        "line_tables": [head["f878"]["n"], head["f870"]["n"]],
        "environment_and_bom": [head["nenv"], head["fab8"] is not None],
    }


def omit(head, selected):
    if "viewport" in selected:
        sheet = head["model"]["f1430"]
        sheet["has_f430"] = 0
        del sheet.f["f430"]
    if "line_tables" in selected:
        head["f878"] = {"n": 0, "styles": []}
        head["f870"].f.update(n=0, f10=[])
    if "environment_and_bom" in selected:
        head.f.update(nenv=0, faf8=[], fab8=None)


def encode(head, reg):
    store = Store(1, reg, 19000)
    reg.run_store("uiModelDoc_c.Serialize", store, head.f, head)
    reg.run_store("uiDrawingDoc_c.Serialize.own", store, head.f, head)
    return bytes(store.out), store.count


def decode(archive, reg):
    doc, load = load_definition(archive.require(DEFINITION), reg, 19000, archive=archive, name=DEFINITION)
    require(doc.head.cls == "uiDrawingDoc_c" and not doc.tail and not load.left(), "expected a complete typed drawing Definition")
    require(doc.head["model"]["f1430"].cls == "moDrSheet", "drawing has no active sheet owner")
    return doc.head, load.count


def variant(raw, selected):
    reg = registry()
    archive = SldprtArchive.from_bytes(raw)
    head, base_count = decode(archive, reg)
    original = values(head)
    require(original == {"viewport": True, "line_tables": [7, 40], "environment_and_bom": [1, True]},
            "disclosed source has a different UI shape")
    before = archive.require(DEFINITION)
    require(encode(head, reg) == (before, base_count), "native control failed typed whole-stream identity")
    omit(head, selected)
    after, count = encode(head, reg)
    streams = dict(archive.streams)
    streams[DEFINITION] = after
    signature, types = TemplateFields(raw, archive)
    payload = EmitSldprt(list(streams.items()), archive.file_id, archive.format_version, signature, types)
    reparsed = SldprtArchive.from_bytes(payload)
    new_head, new_count = decode(reparsed, reg)
    require(encode(new_head, reg) == (after, count) and count == new_count, "typed UI diagnostic did not round-trip")
    current = values(new_head)
    changed_streams = [name for name in archive.streams if archive.streams[name] != reparsed.require(name)]
    require(changed_streams == ([DEFINITION] if selected else []), "UI diagnostic changed an unrelated stream")
    require([key for key in original if original[key] != current[key]] == list(selected), "the selected UI owners differ from the declared diagnostic")
    require(reparsed.streams == streams and TemplateFields(payload, reparsed) == (signature, types),
            "native logical stream or container identity changed during repacking")
    return payload, {"before": original, "after": current, "changed_streams": changed_streams,
                     "definition_bytes": len(after), "definition_sha256": digest(after), "map_next_index": count}


def prepare(prior, pinned, output):
    require(not output.exists() and not output.is_relative_to(ROOT), "UI staging requires a new directory outside the repository")
    pair = read_prior(prior, pinned)
    pristine, reduced, _, _ = pair["cases"]
    first, base = (prior_input(prior.parent, row).read_bytes() for row in (pristine, reduced))
    require(digest(first) == pristine["sha256"] and digest(base) == reduced["sha256"], "blank drawing source changed while staging")
    output.mkdir()
    tools = output / "Tools"
    tools.mkdir()
    tool_hashes = {}
    for name in TOOL_NAMES:
        code = (TOOLS / name).read_bytes()
        (tools / name).write_bytes(code)
        tool_hashes[name] = digest(code)
    rows = []
    for name, selected in CASES:
        payload, verification = (first, None) if name == "Pristine" else variant(base, selected)
        row = {"name": name, "omitted": selected, "sha256": digest(payload), "bytes": len(payload),
               "expected": pristine["expected"], "offline": verification}
        destination = input_path(output, row)
        destination.parent.mkdir(parents=True)
        destination.write_bytes(payload)
        rows.append(row)
    request = {"schema": SCHEMA, "writer_output_count": 0, "native_acceptance": False, "source_pair_sha256": pinned,
               "reduced_control_sha256": reduced["sha256"], "control_sha256": pristine["sha256"],
               "oracle_sha256": pair["oracle_sha256"], "tool_hashes": tool_hashes, "cases": rows}
    packet = output / "Trial.json"
    raw = (json.dumps(request, indent=2, allow_nan=False) + "\n").encode()
    packet.write_bytes(raw)
    read_packet(packet, digest(raw))
    return digest(raw)


def main():
    parser = argparse.ArgumentParser(description="Stage typed drawing UI diagnostics made from the disclosed native control")
    parser.add_argument("prior", type=Path)
    parser.add_argument("--prior-sha256", required=True)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    print(prepare(args.prior.resolve(), args.prior_sha256, args.out.resolve()))


if __name__ == "__main__":
    main()
