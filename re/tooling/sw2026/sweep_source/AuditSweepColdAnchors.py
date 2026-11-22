from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
from struct import unpack
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from InspectPartEnvironmentSource import Image


PINS = {
    "sldmodu.dll": "569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e",
    "sldarchiveu.dll": "5f743916826fd26a25c8d4792ada785d414d1c718c32495e481b1c5dc512ac48",
    "sldcoreu.dll": "3af88769b06bf7a1510fe52f279fbda20e5dc5548dc3925a1357e0f71cc3b3e3",
}
MODEL, ARCHIVE, CORE = PINS
SPANS = {
    "Sweep constructor": (MODEL, 0x4cb3d4d0, 0x4cb3d5ec),
    "Embedded sweep constructor": (MODEL, 0x4cb4f2c0, 0x4cb4f5b7),
    "Embedded sweep arguments and stored words": (MODEL, 0x4cb52816, 0x4cb528d8),
    "Fresh Standard argument forwarding": (MODEL, 0x4cb46485, 0x4cb46574),
    "Component profile wrapper allocation": (MODEL, 0x4cb5d7b9, 0x4cb5d86a),
    "General curve resolution and cache assignment": (MODEL, 0x4c3211d0, 0x4c321789),
    "Reference last-access stamp": (MODEL, 0x4c3290f0, 0x4c3291f4),
    "Same-model update stamp boundary": (MODEL, 0x4bdac640, 0x4bdac699),
    "Live header update stamp getter": (ARCHIVE, 0x319f9810, 0x319f9814),
    "Node flag OR": (MODEL, 0x4c03ed80, 0x4c03ed8e),
    "No sketch block selection state": (MODEL, 0x4cb54000, 0x4cb5400e),
}
EDGES = (
    (0x4cb3d507, 0x4cb4f2c0), (0x4cb3d52b, 0x4c03ed80), (0x4cb3d5a9, 0x4c03ed80),
    (0x4cb4656f, 0x4cb52420), (0x4cb5d847, 0x4c307770), (0x4c321633, 0x4c30f000), (0x4c321749, 0x4c3290f0),
)
CELLS = {0x4d17d8f0: 0x4c3211d0, 0x4d126308: 0x4bdac640, 0x4d1269b0: 0x4b27cbe0}
CIL = "3fbf007191ae352731aadd2b10215ec62e215d82467cc4bc8a0fd489cc806296"


def check(condition, message):
    if not condition:
        raise ValueError(message)


def measure(folder):
    images = {name: Image(folder / name, value) for name, value in PINS.items()}
    positions = {name: {"module": dll, "byte_span": [hex(a), hex(b)],
                        "sha256": sha256(images[dll].read(a, b)).hexdigest()}
                 for name, (dll, a, b) in SPANS.items()}
    model = images[MODEL]
    for start, target in EDGES:
        op, offset = unpack("<Bi", model.read(start, start + 5))
        check(op == 0xe8 and start + 5 + offset == target, "incorrect native instruction edge")
    for source, target in CELLS.items():
        check(unpack("<Q", model.read(source, source + 8))[0] == target, "incorrect native virtual target")
    owned = model.imports()["0x4cd351a8"]
    check(owned["module"].casefold() == ARCHIVE and owned["name"].startswith("?getCurrentUpdateStamp@moHeader_c@@"),
          "wrong native model header getter")
    check(positions["Live header update stamp getter"]["sha256"] ==
          "68b70ba1e6ad2356c69cac8e846649e599945994fa7690a0bf4af28fa25c24a5",
          "header accessor no longer reads its f40 word")
    core = images[CORE]
    method = core.base + 0x15eac0
    header = core.read(method, method + 12)
    flags, _, code_size, _ = unpack("<HHII", header)
    code = core.read(method + 12, method + 12 + code_size)
    check(flags >> 12 == 3 and sha256(code).hexdigest() == CIL
          and unpack_from_call(code, 1756) == 0x06004687, "incorrect managed sweep initializer call")
    return {"schema": "kit.sw2026.cold-sweep-physical-anchors.v1", "modules": PINS, "spans": positions,
            "native_edges": [[hex(start), hex(target)] for start, target in EDGES],
            "virtual_targets": {hex(source): hex(target) for source, target in CELLS.items()},
            "header_import": owned, "managed_methods": [{"module": CORE,
                "name": "CreateSweepPacket_c.Apply", "methoddef": "0x060053fc", "rva": "0x15eac0",
                "code_sha256": CIL, "code_size": code_size, "sweep_initializer_call_code_offset": 1756,
                "target_methoddef": "0x06004687"}],
            "native_execution": False, "vendor_body_or_code_emitted": False}


def unpack_from_call(code, offset):
    opcode, token = unpack("<BI", code[offset:offset + 5])
    check(opcode == 0x28, "expected a managed direct call")
    return token


if __name__ == "__main__":
    argv = ArgumentParser()
    argv.add_argument("--licensed-bin", type=Path, required=True)
    print(json.dumps(measure(argv.parse_args().licensed_bin), sort_keys=True, indent=2, allow_nan=False))
