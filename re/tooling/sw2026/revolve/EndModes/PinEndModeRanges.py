from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
from runpy import run_path
from struct import unpack_from
import json

TOOLS = Path(__file__).resolve().parents[2]
MODEL_SHA = "569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e"
HELPERS = {
    "PinNativeNames.py": "ffa6f015b152d2aa0ce869afc94665e5f01f5089d23298fa19681ff2ac7dc7b9",
    "PinAtomNames.py": "be54e65e7add981f20a1926b2e157b9879a4797706500d4d4dfbabaa3e158f45",
}
RANGES = (
    ("end_serializer", 0x4BB1E320, 0x4BB1E5E9),
    ("feature_serializer", 0x4BB1E7A0, 0x4BB1ED0D),
    ("end_constructor", 0x4C38A4C0, 0x4C38A699),
    ("feature_constructor", 0x4C38AA40, 0x4C38ACE1),
    ("direction2_angle", 0x4C396120, 0x4C3961CC),
    ("end_angle_by_side", 0x4C3961D0, 0x4C396257),
    ("direction1_angle", 0x4C396260, 0x4C39631B),
    ("angle_display_by_side", 0x4C396320, 0x4C3963A6),
    ("effective_axis", 0x4C3964F0, 0x4C396575),
    ("effective_single_end", 0x4C39AC10, 0x4C39AC1F),
    ("linked_mode_and_sweep", 0x4C39B2B0, 0x4C39E376),
    ("second_sweep_path", 0x4C3A4700, 0x4C3A6957),
    ("remove_inactive_angle_displays", 0x4C3A7510, 0x4C3A7645),
    ("private_revolve_type", 0x4B37FB30, 0x4B37FB37),
    ("reverse_direction", 0x4B37FB40, 0x4B37FB47),
)
SLOTS = (
    0x4CD3A980, 0x4CD3B7F8, 0x4CD386D0, 0x4CD38EC8, 0x4CD3C010,
    0x4CD3D970, 0x4CD3D880, 0x4CD3D888, 0x4CD36458,
)


def pin_ranges(path):
    if any((parent / ".git").exists() for parent in path.parents):
        raise ValueError("the licensed module must be outside Git checkouts")
    helper = {}
    for name, expected in HELPERS.items():
        source = TOOLS / "body" / name
        if sha256(source.read_bytes()).hexdigest() != expected:
            raise ValueError("pinned PE helper differs")
        helper[name] = run_path(str(source))
    image = helper["PinNativeNames.py"]["Image"](path)
    if (len(image.data), image.base, sha256(image.data).hexdigest()) != (
        46536280, 0x4B140000, MODEL_SHA
    ):
        raise ValueError("licensed model module differs from SOLIDWORKS 2026 SP05.2")
    imports = helper["PinAtomNames.py"]["imports"](image)
    return {
        "schema": "kit.sw2026.revolve-end-mode-static-pins.v1",
        "module": path.name, "module_sha256": MODEL_SHA,
        "image_base": hex(image.base), "module_bytes": len(image.data),
        "tool_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "helper_sha256": HELPERS,
        "effective_axis_vtable": {
            "address": hex(0x4D185908), "slot": hex(0x1788),
            "target": hex(unpack_from("<Q", image.at(0x4D185908 + 0x1788, 8))[0]),
        },
        "ranges": [{
            "role": name, "start": hex(start), "end_exclusive": hex(end),
            "file_offset": image.offset(start - image.base, end - start),
            "sha256": sha256(image.at(start, end - start)).hexdigest(),
        } for name, start, end in RANGES],
        "imports": {hex(slot): imports[slot] for slot in SLOTS},
        "numeric_literals": {
            hex(address): unpack_from("<d", image.at(address, 8))[0]
            for address in (0x4CD9A3C0, 0x4D18B9E0, 0x4CDFEC80)
        },
        "native_execution": False,
    }


def main():
    parser = ArgumentParser(description="Pin exact-build ordinary revolve mode routines")
    parser.add_argument("model", type=Path)
    args = parser.parse_args()
    print(json.dumps(pin_ranges(args.model.resolve(strict=True)), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
