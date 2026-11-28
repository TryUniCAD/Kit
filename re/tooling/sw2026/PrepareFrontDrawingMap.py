from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from shutil import copyfile

ROOT = Path(__file__).resolve().parents[3]
TOOLS = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT / "src"), str(TOOLS / "serial")]

from CheckDrawingDefinitions import SOURCE_LOCK, check_header, checked_artifacts, compare_sheet, digest, require
from Classes import registry
from Core import Store
from InspectFrontDrawingMap import PART_FILE, SCHEMA, SOURCES, TOOL_NAMES, VARIANTS
from convert.adapters.solidworks.Container.Container import EmitSldprt, SldprtArchive, TemplateFields
from defs.Definition import load_definition


DEFINITION = "Contents/Definition"


def encode(definition, rules):
    archive = Store(1, rules, 19000)
    rules.run_store("uiModelDoc_c.Serialize", archive, definition.head.f, definition.head)
    rules.run_store("uiDrawingDoc_c.Serialize.own", archive, definition.head.f, definition.head)
    require(not definition.tail, "diagnostic drawing Definition has an unclassified tail")
    return bytes(archive.out), archive.count


def diagnostic_variants(payload, saved, reopened, rules):
    native = SldprtArchive.from_bytes(payload)
    require(native.format_version == 4, "drawing diagnostic requires container version 4")
    start = native.require(DEFINITION)
    definition, original = load_definition(start, rules, 19000)
    require(encode(definition, rules) == (start, original.count), "native drawing Definition did not round-trip")
    model = definition.head["model"]
    require(model["n1578"] == len(model["f1570"]) == 1 and model["f1570"][0]["n"] == 4,
            "front drawing diagnostic requires a populated rectangular edge map")
    model.f.update(n1578=0, f1570=[])
    altered, next_index = encode(definition, rules)
    readback, reader = load_definition(altered, rules, 19000)
    require(encode(readback, rules) == (altered, reader.count) and not readback.head["model"]["f1570"], "omitted map stream failed exact readback")
    header, _ = check_header(native.require("Header2"), rules)
    compare_sheet(readback.head["model"], header, saved, reopened)
    signatures, type_ids = TemplateFields(payload, native)
    streams = native.streams
    changed = {**streams, DEFINITION: altered}
    repacked, omitted = (EmitSldprt(list(values.items()), native.file_id, native.format_version, signatures, type_ids)
                         for values in (streams, changed))
    require(SldprtArchive.from_bytes(repacked).streams == streams and SldprtArchive.from_bytes(omitted).streams == changed,
            "drawing diagnostic repack changed a logical stream")
    evidence = {"definition_map_before": original.count, "definition_map_after": next_index,
                "definition_bytes_before": len(start), "definition_bytes_after": len(altered),
                "stream_roles": list(streams), "changed_streams": [DEFINITION]}
    return (payload, repacked, omitted), evidence


def prepare(corpus, output):
    require(not output.resolve().is_relative_to(ROOT) and not output.exists(), "choose an unused diagnostic directory outside the checkout")
    lock_data = SOURCE_LOCK.read_bytes()
    lock = json.loads(lock_data)
    cases = {case["name"]: case for case in lock["cases"] if case["name"] in SOURCES and case["split"] == "discovery"}
    rules = registry()
    rows = []
    for name in SOURCES:
        payload, saved, reopened = checked_artifacts(corpus, cases[name])
        child = (corpus / name / "author" / PART_FILE).read_bytes()
        require(digest(child) == lock["reference_part_sha256"], "front drawing reference part differs from its locked authoring source")
        variants, evidence = diagnostic_variants(payload, saved, reopened, rules)
        variant_rows = []
        for label, data in zip(VARIANTS, variants, strict=True):
            destination = output / name / label
            destination.mkdir(parents=True, exist_ok=False)
            (destination / (name + ".SLDDRW")).write_bytes(data)
            (destination / PART_FILE).write_bytes(child)
            variant_rows.append({"name": label, "sha256": digest(data), "bytes": len(data)})
        rows.append({"name": name, "cases": variant_rows, "expected": saved, "part_sha256": digest(child), **evidence})
    packet = {"schema": SCHEMA, "writer_output_count": 0, "native_acceptance": False, "cases": rows,
              "oracle_sha256": lock["oracle_sha256"], "source_lock_sha256": digest(lock_data)}
    packet_path = output / "PrivateManifest.json"
    packet_bytes = (json.dumps(packet, sort_keys=True, indent=2) + "\n").encode()
    packet_path.write_bytes(packet_bytes)
    guest = output / "Tools"
    guest.mkdir(exist_ok=False)
    for tool in TOOL_NAMES:
        copyfile(TOOLS / tool, guest / tool)
    tools = (json.dumps({tool: digest((guest / tool).read_bytes()) for tool in TOOL_NAMES}, sort_keys=True, indent=2) + "\n").encode()
    (guest / "GuestTools.json").write_bytes(tools)
    subprocess.run([sys.executable, "-B", str(guest / "InspectFrontDrawingMap.py"), str(packet_path),
                    "--packet-sha256", digest(packet_bytes), "--tools-sha256", digest(tools), "--verify-only"], check=True, timeout=30)
    return {"packet": str(packet_path), "packet_sha256": digest(packet_bytes), "tools_sha256": digest(tools)}


def main():
    parser = argparse.ArgumentParser(description="Stage the two disclosed front drawing diagnostics outside the checkout")
    parser.add_argument("corpus", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    print(json.dumps(prepare(args.corpus, args.output), sort_keys=True))


if __name__ == "__main__":
    main()
