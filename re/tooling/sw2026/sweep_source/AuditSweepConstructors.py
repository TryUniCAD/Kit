from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
from struct import unpack
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from InspectPartEnvironmentSource import Image


MODEL = "sldmodu.dll"
GEOMETRY = "sldgcu.dll"
BRIDGE = "sldgciParau.dll"
MODULES = {
    MODEL: (0x4b140000, "569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e"),
    GEOMETRY: (0x43740000, "77b7376933f483eb5c1e3a93e22241f07a001a824023f5498d880d9b45fae594"),
    BRIDGE: (0x32f70000, "96f244063a5e8badc547fca3655506ae8eb99197653168efa232d775b55b96ce"),
}
SPANS = {
    "Sweep initializer": (MODEL, 0x4cb460f0, 0x4cb467f1),
    "Embedded initializer": (MODEL, 0x4cb52420, 0x4cb529f2),
    "Section setter and parent dispatch": (MODEL, 0x4cb67230, 0x4cb6733b),
    "Section array copy": (MODEL, 0x4cb53e70, 0x4cb53e82),
    "Path contact choice": (MODEL, 0x4cb668f0, 0x4cb66b46),
    "Ghost ID getter": (MODEL, 0x4b282e20, 0x4b282e24),
    "Root ghost manager getter": (MODEL, 0x4b286de0, 0x4b286de8),
    "Ghost manager constructor": (MODEL, 0x4bf03a90, 0x4bf03ba5),
    "Ghost ID increment": (MODEL, 0x4bf0aef0, 0x4bf0af1d),
    "Ghost allocation and component assignment": (MODEL, 0x4bf08a80, 0x4bf08ba7),
    "Shared ghost ID setter": (MODEL, 0x4b2ad1e0, 0x4b2ad1e4),
    "Ghost record constructor": (MODEL, 0x4bf03c90, 0x4bf03ea5),
    "Ghost row kind dispatch": (MODEL, 0x4b7fa350, 0x4b7fa377),
    "Ghost manager store and flags": (MODEL, 0x4bf050e0, 0x4bf05381),
    "General curve wrapper constructor": (MODEL, 0x4c307770, 0x4c3078ff),
    "Shared reference wrapper constructor": (MODEL, 0x4c308370, 0x4c3084b9),
    "Wire contact constructor": (MODEL, 0x4cb69ed0, 0x4cb69f22),
    "Contact defaults": (MODEL, 0x4cb69c20, 0x4cb69d65),
    "Component profile constructor": (MODEL, 0x4b815960, 0x4b815ac0),
    "Component feature identity constructor": (MODEL, 0x4bb34370, 0x4bb343af),
    "Set ghost ID export": (GEOMETRY, 0x438a4340, 0x438a4345),
    "Set ghost ID backend branch": (GEOMETRY, 0x43e904b0, 0x43e904ec),
    "Parasolid ghost attribute setter": (BRIDGE, 0x32f83760, 0x32f83a62),
}
EDGES = {
    MODEL: (
        (0x4cb46258, 0x4cb67230, 0xe8), (0x4cb46263, 0x4cb67220, 0xe8),
        (0x4cb67229, 0x4cb668f0, 0xe9), (0x4cb4631a, 0x4b78cf00, 0xe8),
        (0x4cb463d8, 0x4c0d3270, 0xe8), (0x4cb4656f, 0x4cb52420, 0xe8),
        (0x4b815a0e, 0x4bb34370, 0xe8), (0x4cb69ee5, 0x4cb69c20, 0xe8),
        (0x4c307785, 0x4c308370, 0xe8), (0x4c3223dd, 0x4bf0aef0, 0xe8),
        (0x4bf08ba2, 0x4b2ad1e0, 0xe8),
    ),
    GEOMETRY: ((0x438a4340, 0x43e904b0, 0xe9),),
    BRIDGE: ((0x32f837dc, 0x32fa1260, 0xe8), (0x32f837b6, 0x32fa1430, 0xe8)),
}
CELLS = {0x4ce97210: 0x4b7f9fc0, 0x4ce970b8: 0x4b27e150, 0x4d2e3568: 0x4cb6d1a0}
IMPORTS = {
    MODEL: {0x4cd375b0: "?gc_isGhostingEnabled@@YAHXZ", 0x4cd37f68: "?getBodies@gcPartition_w@@QEAAHXZ"},
    GEOMETRY: {0x43f5a068: "?setGhostId@gciBody_w@GCP@@QEAAXHH@Z"},
}


def collect(directory):
    images = {key: Image(directory / key, digest) for key, (_, digest) in MODULES.items()}
    if any(image.base != MODULES[name][0] for name, image in images.items()):
        raise ValueError("selected exact module has another image base")
    spans = {name: {"module": module, "start": hex(start), "end_exclusive": hex(end),
                    "sha256": sha256(images[module].read(start, end)).hexdigest()}
             for name, (module, start, end) in SPANS.items()}
    edges, virtual, imports = [], {}, {}
    for module, sites in EDGES.items():
        for start, target, opcode in sites:
            sequence = images[module].read(start, start + 5)
            if sequence[0] != opcode or start + 5 + unpack("<i", sequence[1:])[0] != target:
                raise ValueError("selected native branch target differs")
            edges.append({"module": module, "source": hex(start), "target": hex(target),
                          "kind": "call" if opcode == 0xe8 else "jump"})
    for slot, target in CELLS.items():
        observed, = unpack("<Q", images[MODEL].read(slot, slot + 8))
        if observed != target:
            raise ValueError("selected native vtable target differs")
        virtual[hex(slot)] = hex(target)
    for module, sites in IMPORTS.items():
        table = images[module].imports()
        for location, symbol in sites.items():
            row = table[hex(location)]
            if row["name"] != symbol:
                raise ValueError("selected native imported producer differs")
            imports[hex(location)] = {"source_module": module, **row}
    return {"schema": "kit.sw2026.sweep-constructor-anchors.v1", "modules": MODULES, "windows": spans,
            "edges": edges, "virtual_cells": virtual, "imports": imports, "native_execution": False,
            "supports_public_writer": False}


if __name__ == "__main__":
    parser = ArgumentParser(description="Fingerprint the exact licensed 2026 constructor anchors")
    parser.add_argument("--licensed-bin", type=Path, required=True)
    print(json.dumps(collect(parser.parse_args().licensed_bin), sort_keys=True, indent=2, allow_nan=False))
