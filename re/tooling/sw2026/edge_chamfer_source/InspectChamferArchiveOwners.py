from argparse import ArgumentParser
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "materials"))

from MaterialPe import PeImage

MODULES = {
    "sldmopartu.dll": ("aa3fa88eeb5349c8ac2161ce9b3f18ab4e23417598c6b57719c88d5d6c178da9",
                     (0x18023eb30, 0x18023eba2, 0x18023ec0e, 0x18023ecdf,
                      0x18023ed8e, 0x18023edbc, 0x18023ef1e, 0x18023f13b,
                      0x18023f26b, 0x18023f3b0)),
    "sldmodu.dll": ("569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e",
                   (0x4c82c020,)),
    "sldmfcu.dll": ("af2148c7f429e017e75de45b27acf4105b80457fa510dffaa25db88c387a9735",
                   (0x3c857330,)),
}


def owner(image, addresses):
    intervals = set()
    leaves = []
    for address in addresses:
        bounds = image.range(address)
        if bounds is not None:
            intervals.add(bounds)
        else:
            leaves.append(hex(address))
    imports = {key: value for key, value in image.imports().items()
               if "iSerializeEdges@moRefHistHelperFeatData_c" in value["name"]
               or "iSerializeFaces@moRefHistHelperFeatData_c" in value["name"]
               or "Serialize@moBodyFeature_c" in value["name"]}
    return {"image_sha256": image.sha256, "preferred_base": hex(image.base),
            "owned_unwind_regions": [image.pin("unwind region", start, end)
                                     for start, end in sorted(intervals)],
            "anchors_without_unwind_row": leaves,
            "independent_import_roles": {hex(address): row for address, row in imports.items()}}


def inspect(directory):
    directory = directory.resolve(strict=True)
    if directory.is_relative_to(ROOT):
        raise ValueError("licensed original modules belong outside the checkout")
    found = {}
    for name, (expected, addresses) in MODULES.items():
        image = PeImage(directory / name)
        if image.sha256 != expected:
            raise ValueError("original SOLIDWORKS 2026 SP05.2 image differs: " + name)
        found[name] = owner(image, addresses)
    return {"schema": "kit.sw2026.edge-chamfer-archive-owner.v1", "build": "34.5.2.0604",
            "binary_modules": found, "native_processes": 0, "cad_payloads_read": 0}


if __name__ == "__main__":
    args = ArgumentParser()
    args.add_argument("licensed_directory", type=Path)
    options = args.parse_args()
    print(json.dumps(inspect(options.licensed_directory), indent=2, sort_keys=True, allow_nan=False))
