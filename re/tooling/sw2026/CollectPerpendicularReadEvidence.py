import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from CollectDrawingViewSupportEvidence import Image, module, require
from CollectPerpendicularEvidence import word


EXPECTED_MODULE = "569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e"
SLOTS = {
    1000: (0x4BB2A650, "moFeature_c.SerializeXmlData"),
    1016: (0x4C03E170, "moNode_c.getIdForXmlDataExtracter"),
    1208: (0x4C17A7B0, "moConcept_c.SerializeLWData"),
    1216: (0x4C17B570, "moConcept_c.SerializeResolvedData"),
}


def collect(path):
    image = Image(path)
    identity = module(image, EXPECTED_MODULE)
    rows = []
    for offset, (expected, role) in SLOTS.items():
        perpendicular = word(image, 0x4CFA2278 + offset)
        parallel = word(image, 0x4CF9FE10 + offset)
        require(perpendicular == parallel == expected, "the exact concrete archive virtual changed")
        rows.append({"slot_bytes": offset, "perpendicular_target": hex(perpendicular),
                     "parallel_target": hex(parallel), "shared_rule": role,
                     "routine_identity": image.function(perpendicular)})
    lifecycle = []
    for offset, target in ((0x230, 0x4B28E090), (0x238, 0x4B30F9F0)):
        require(word(image, 0x4CFA2278 + offset) == word(image, 0x4CF9FE10 + offset) == target,
                "the exact inherited node update predicate changed")
        lifecycle.append({"slot_bytes": offset, "target": hex(target), "routine_identity": image.function(target)})
    return {"schema": "kit.sw2026.perpendicular-mate-reader-bindings.v1", "archive_version": 19000,
            "module": identity, "perpendicular_primary_table": "0x4cfa2278", "parallel_primary_table": "0x4cf9fe10",
            "shared_serialization_entry": "0x4b668a60", "shared_base": "moMate2Geoms_c", "virtuals": rows,
            "inherited_node_lifecycle": lifecycle,
            "scope": "exact concrete archive framing only; solver behavior remains separately measured",
            "script_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
            "native_processes_started": 0, "heldout_inputs_read": False, "writer_output_count": 0}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), "choose a new numeric evidence output")
    data = (json.dumps(collect(args.module), indent=2, sort_keys=True) + "\n").encode()
    args.output.write_bytes(data)
    print(json.dumps({"sha256": sha256(data).hexdigest(), "virtual_count": 4, "native_processes_started": 0}))


if __name__ == "__main__":
    main()
