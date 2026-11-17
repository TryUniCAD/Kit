from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "src"), str(Path(__file__).resolve().parent / "serial")]

from CheckDrawingDefinitions import digest, reencode, require
from Classes import registry
from convert.adapters.solidworks.Container.Container import SldprtArchive, TemplateFields


BASELINE_RECEIPT = ROOT / "re/solidworks/measurements/2026/GeneratedBlankDrawingCandidate01.json"
DEFINITION = "Contents/Definition"


def compare(baseline, candidate):
    receipt_bytes = BASELINE_RECEIPT.read_bytes()
    earlier = json.loads(receipt_bytes)["generated"][0]
    require(digest(baseline) == earlier["native_sha256"], "baseline must be the frozen first blank drawing candidate")
    archives = [SldprtArchive.from_bytes(payload) for payload in (baseline, candidate)]
    before, after = archives
    require(before.format_version == after.format_version == 4 and before.file_id == after.file_id,
            "candidate changed the version or file identity")
    require(TemplateFields(baseline, before) == TemplateFields(candidate, after), "candidate changed container tags")
    old_streams, new_streams = before.streams, after.streams
    require(old_streams.keys() == new_streams.keys(), "candidate changed stream roles")
    changed = sorted(name for name, data in old_streams.items() if data != new_streams[name])
    require(changed == [DEFINITION], "only Definition may change")
    old, new = (archive.require(DEFINITION) for archive in archives)
    offsets = [offset for offset, (left, right) in enumerate(zip(old, new, strict=True)) if left != right]
    decoded = [reencode(archive.require(DEFINITION), registry(), archive) for archive in archives]
    values = [model["fd50"] for model, _ in decoded]
    counts = [count for _, count in decoded]
    require(values == [1, 0] and counts[0] == counts[1] and len(offsets) == 1,
            "Definition must reencode exactly with one changed byte in the cosmetic-thread result")
    offset, = offsets
    require(old[offset:offset + 4] == (1).to_bytes(4, "little") and new[offset:offset + 4] == bytes(4),
            "the changed byte must be the low byte of the stored signed flag")
    streams = {name: {"bytes": len(data), "before_sha256": digest(data), "after_sha256": digest(new_streams[name])}
               for name, data in old_streams.items()}
    return {"schema": "kit.sw2026.blank-drawing-cosmetic-thread.v1", "baseline_receipt_sha256": digest(receipt_bytes),
            "baseline_sha256": digest(baseline), "candidate_sha256": digest(candidate), "candidate_bytes": len(candidate),
            "native_acceptance": False, "changed_streams": changed, "definition_changed_byte_offsets": offsets,
            "definition_next_map_index": counts[0], "cosmetic_thread_flag": values, "streams": streams}


def main():
    parser = argparse.ArgumentParser(description="Verify the isolated cosmetic-thread correction to the frozen blank drawing")
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    args = parser.parse_args()
    print(json.dumps(compare(args.baseline.read_bytes(), args.candidate.read_bytes()), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
