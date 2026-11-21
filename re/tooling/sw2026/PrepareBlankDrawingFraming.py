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

from CheckDrawingDefinitions import SOURCE_LOCK, check_header, checked_artifacts, compare_sheet, digest, reencode, require
from Classes import registry
from InspectBlankDrawingFraming import CASES, SCHEMA, TOOL_NAMES, input_path
from convert.adapters.solidworks.Container.Container import CentralMarks, SldprtArchive, TemplateFields, build_sldprt


SAVES = ROOT / "re/solidworks/measurements/2026/GeneratedBlankDrawingSaveModes03.json"
DISCLOSED = "D00EmptySheet"


def encode_json(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def words(payload, archive):
    records = tuple(sorted(archive.records, key=lambda entry: entry.offset))
    rows = {(entry.name, entry.crc32, entry.compressed_size, entry.uncompressed_size) for entry in records}
    directory = CentralMarks(payload, records, rows)
    require(len(directory) == len(records), "drawing framing requires a complete physical directory")
    result = {"file-id": 0, "directory-end-signature": len(payload) - 22}
    for entry, center in zip(records, directory, strict=True):
        label = entry.name
        result.update({f"local-signature:{label}": entry.offset - 4, f"local-record-word:{label}": entry.offset + 6,
                       f"directory-signature:{label}": center - 6, f"directory-record-word:{label}": center + 6})
    return result


def compare_physical(before, after, original, reframed):
    require(original.streams == reframed.streams and original.format_version == reframed.format_version == 4,
            "drawing refactoring changed a logical stream")
    require(len(before) == len(after), "the two containers need identical extents")
    owned = words(before, original)
    require(owned == words(after, reframed), "matching physical records must retain their archive offsets")
    allowed = {index for offset in owned.values() for index in range(offset, offset + 4)}
    actual = {index for index, (left, right) in enumerate(zip(before, after, strict=True)) if left != right}
    require(actual and actual <= allowed, "unexpected bytes changed outside the file, signature and stream-record words")
    return {"changed_bytes": len(actual), "changed_words": [
        {"role": role, "offset": offset, "vendor_bytes": before[offset:offset + 4].hex(), "kit_bytes": after[offset:offset + 4].hex()}
        for role, offset in sorted(owned.items(), key=lambda item: item[1]) if before[offset:offset + 4] != after[offset:offset + 4]
    ]}


def framing_comparison(reduced, pristine, expected, reopened):
    source = SldprtArchive.from_bytes(reduced)
    control = SldprtArchive.from_bytes(pristine)
    require(len(source.streams) == 7 and source.streams.keys() < control.streams.keys(), "expected the previously measured native blank reduction")
    require(all(payload == control.require(name) for name, payload in source.streams.items()), "the native reduction changed a logical stream")
    generated_framing = build_sldprt(source.streams)
    alternate = SldprtArchive.from_bytes(generated_framing)
    physical = compare_physical(reduced, generated_framing, source, alternate)
    rules = registry()
    model, count = reencode(alternate.require("Contents/Definition"), rules, alternate)
    header, header_count = check_header(alternate.require("Header2"), rules)
    compare_sheet(model, header, expected, reopened)
    frames = []
    for payload, archive in ((reduced, source), (generated_framing, alternate)):
        signatures, type_ids = TemplateFields(payload, archive)
        frames.append({"file_id": archive.file_id, "signatures": [value.hex() for value in signatures], "record_words": type_ids,
                       "sha256": digest(payload), "bytes": len(payload)})
    return generated_framing, {"vendor_framing": frames[0], "kit_framing": frames[1], "container_version": source.format_version,
                              "logical_streams_identical": True, "definition_map_next_index": count, "header_map_next_index": header_count,
                              "streams": {name: {"bytes": len(data), "sha256": digest(data)} for name, data in source.streams.items()},
                              **physical}


def prepare(corpus, reduced, output):
    output = output.resolve()
    require(not output.exists() and not output.is_relative_to(ROOT), "choose an unused private framing output")
    lock_data, saves_data = SOURCE_LOCK.read_bytes(), SAVES.read_bytes()
    lock, saves = json.loads(lock_data), json.loads(saves_data)
    require(lock["passed"] and saves["controls_healthy"] and saves["inputs_immutable"] and lock["oracle_sha256"] == saves["oracle_sha256"],
            "framing comparison requires the qualified blank-drawing source and native reduced saves")
    case, = [row for row in lock["cases"] if row["name"] == DISCLOSED and row["split"] == "discovery"]
    pristine, saved, reopened = checked_artifacts(corpus, case)
    baseline = reduced.read_bytes()
    known_modes = [row for row in saves["modes"] if row["source_kind"] == "native-stream-reduction"]
    require(len(known_modes) == 2 and all(row["passed"] and row["input_sha256"] == digest(baseline) for row in known_modes),
            "the reduced blank differs from the native save-mode evidence")
    changed, evidence = framing_comparison(baseline, pristine, saved, reopened)
    rows = []
    for name, payload in zip(CASES, (pristine, baseline, changed), strict=True):
        row = {"name": name, "bytes": len(payload), "sha256": digest(payload), "expected": saved}
        target = input_path(output, row)
        target.parent.mkdir(parents=True, exist_ok=False)
        target.write_bytes(payload)
        rows.append(row)
    offline = encode_json(evidence)
    (output / "PhysicalComparison.json").write_bytes(offline)
    guest = output / "Tools"
    guest.mkdir(exist_ok=False)
    for name in TOOL_NAMES:
        copyfile(TOOLS / name, guest / name)
    tool_hashes = {name: digest((guest / name).read_bytes()) for name in TOOL_NAMES}
    packet = {"schema": SCHEMA, "writer_output_count": 0, "native_acceptance": False, "control_sha256": digest(pristine),
              "source_lock_sha256": digest(lock_data), "native_save_modes_sha256": digest(saves_data), "oracle_sha256": lock["oracle_sha256"],
              "offline_sha256": digest(offline), "tool_hashes": tool_hashes, "cases": rows}
    path = output / "Trial.json"
    raw = encode_json(packet)
    path.write_bytes(raw)
    packet_hash = digest(raw)
    subprocess.run([sys.executable, "-B", str(guest / "InspectBlankDrawingFraming.py"), str(path),
                    "--packet-sha256", packet_hash, "--verify-only"], check=True, timeout=30)
    return {"packet": str(path), "packet_sha256": packet_hash, "offline_sha256": digest(offline), "tool_hashes": tool_hashes,
            "case_hashes": {row["name"]: row["sha256"] for row in rows}}


def main():
    parser = argparse.ArgumentParser(description="Stage a source-preserving blank-drawing framing experiment")
    for name in ("corpus", "reduced", "output"):
        parser.add_argument(name, type=Path)
    arguments = parser.parse_args()
    print(json.dumps(prepare(arguments.corpus, arguments.reduced, arguments.output), sort_keys=True))


if __name__ == "__main__":
    main()
