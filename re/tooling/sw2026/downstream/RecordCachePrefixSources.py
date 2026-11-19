from argparse import ArgumentParser
from json import dumps
from pathlib import Path
from struct import iter_unpack, unpack_from

from materials.MaterialPe import PeImage


MODEL = "sldmodu.dll"
ARCHIVE = "sldarchiveu.dll"
IMAGE_DIGESTS = {
    MODEL: "569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e",
    ARCHIVE: "5f743916826fd26a25c8d4792ada785d414d1c718c32495e481b1c5dc512ac48",
}
FUNCTIONS = (
    (MODEL, "part constructor", 0x4c19f170, None),
    (MODEL, "owned model header getter", 0x4b285b20, 0x4b285b28),
    (MODEL, "part cache creation caller", 0x4b578680, None),
    (MODEL, "part cache update caller", 0x4b58f550, None),
    (MODEL, "fresh cache finalization", 0x4b5263c0, None),
    (MODEL, "cache update finalization", 0x4b53a480, None),
    (MODEL, "cache freshness predicate", 0x4b535b80, None),
    (ARCHIVE, "header update-counter getter", 0x319f9810, 0x319f9814),
)
WINDOWS = (
    ("install part table", 0x4c19f1cd, 0x4c19f1d7),
    ("fresh finalization call", 0x4b57881d, 0x4b578829),
    ("update finalization call", 0x4b58f759, 0x4b58f765),
    ("fresh header values", 0x4b5267d7, 0x4b526829),
    ("updated header owner", 0x4b53a509, 0x4b53a530),
    ("updated header values", 0x4b53ab5c, 0x4b53ab95),
    ("cache and current update times", 0x4b535b89, 0x4b535bad),
)
HEADER_IMPORTS = (0x4cd33d00, 0x4cd33cf8, 0x4cd3d580, 0x4cd351a8)


def function_fragments(image, address, leaf_end):
    if leaf_end is not None:
        return [image.pin("complete leaf", address, leaf_end)]
    rva, size = unpack_from("<II", image.data, image.optional + 112 + 3 * 8)
    offset = image.offset(image.base + rva)
    entries = tuple(iter_unpack("<III", image.data[offset:offset + size]))

    def root(entry):
        visited = set()
        while entry not in visited:
            visited.add(entry)
            unwind = image.offset(image.base + entry[2])
            flags, count = image.data[unwind] >> 3, image.data[unwind + 2]
            if not flags & 4:
                return entry
            entry = unpack_from("<III", image.data, unwind + 4 + ((count + 1) & ~1) * 2)
        raise ValueError("cycle in PE unwind chain")

    target = address - image.base
    selected, = (entry for entry in entries if entry[0] <= target < entry[1])
    owner = root(selected)
    fragments = (entry for entry in entries if root(entry) == owner)
    return [
        image.pin("complete unwind fragment", image.base + first, image.base + last)
        for first, last, _ in fragments
    ]


def main():
    parser = ArgumentParser()
    parser.add_argument("--bin-directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    images = {name: PeImage(args.bin_directory / name) for name in IMAGE_DIGESTS}
    if any(images[name].sha256 != digest for name, digest in IMAGE_DIGESTS.items()):
        raise ValueError("supplied modules differ from the original 2026 SP05.2 images")
    model = images[MODEL]
    archive = images[ARCHIVE]
    imports = model.imports()
    getter_name = imports[0x4cd351a8]["name"]
    getter, = (row for row in archive.exports() if row["name"] == getter_name)
    cell = 0x4d1252d8 + 0x11f0
    target = model.u64(model.offset(cell))
    if target != 0x4b285b20 or getter["address"] != "0x319f9810":
        raise ValueError("the selected header getter dispatch differs")
    record = {
        "schema": "kit.sw2026.downstream-cache-prefix-sources.v1",
        "build": "34.5.2.0604",
        "modules": [
            {"name": name, "sha256": image.sha256, "bytes": len(image.data), "base": hex(image.base)}
            for name, image in images.items()
        ],
        "functions": [
            {"name": name, "module": module, "entry": hex(entry),
             "fragments": function_fragments(images[module], entry, leaf_end)}
            for module, name, entry, leaf_end in FUNCTIONS
        ],
        "instruction_windows": [model.pin(name, first, last) for name, first, last in WINDOWS],
        "part_header_table_cell": model.pin("actual part header target", cell, cell + 8),
        "part_header_target": hex(target),
        "header_update_stamp_import_export": getter,
        "imports": [{"slot": hex(slot), **imports[slot]} for slot in HEADER_IMPORTS],
        "cad_inputs_read": 0,
        "vendor_runs": 0,
    }
    with args.output.open("x", encoding="utf-8") as output:
        output.write(dumps(record, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
