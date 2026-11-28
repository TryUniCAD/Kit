from argparse import ArgumentParser
from pathlib import Path
import json
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path.insert(0, str(HERE.parent.parent / "materials"))

from MaterialPe import PeImage

MODULES = {
    "sldmopartu.dll": (
        "aa3fa88eeb5349c8ac2161ce9b3f18ab4e23417598c6b57719c88d5d6c178da9",
        {"options_accessor": (0x1801F99C0, 0x1801F99C8),
         "runtime_class_initializer": (0x18023E2EC, 0x18023E2F9),
         "edge_initializer": (0x18023E457, 0x18023E464),
         "vertex_initializer": (0x18023E727, 0x18023E734),
         "ordinary_archive_load": (0x18023ECD2, 0x18023ECE2),
         "ordinary_archive_store": (0x18023F12E, 0x18023F142),
         "first_kernel_array_operand": (0x180242ADA, 0x180242BAD),
         "second_kernel_array_operand": (0x1802442BE, 0x180244354)},
        {0x1803EC788: ("swccu.dll", "??0su_CDWordArray"),
         0x1803E9098: ("sldgcu.dll", "?ramChamferEdge")},
    ),
    "sldgcu.dll": (
        "77b7376933f483eb5c1e3a93e22241f07a001a824023f5498d880d9b45fae594",
        {"ordinary_export": (0x43CA0740, 0x43CA0820),
         "kernel_array_argument": (0x43E7F2B3, 0x43E7F2C8),
         "kernel_import_call": (0x43E7F398, 0x43E7F39E)},
        {0x43F5C908: ("sldgciParau.dll", "?gci_ramChamferEdge")},
    ),
    "sldgciParau.dll": (
        "96f244063a5e8badc547fca3655506ae8eb99197653168efa232d775b55b96ce",
        {"array_pointer_capture": (0x3305FA49, 0x3305FA59),
         "empty_and_saved_option_branches": (0x33060A79, 0x33060ABA),
         "success_only_option_capture": (0x33060F59, 0x33060F79),
         "six_slots_from_computed_options": (0x330780D0, 0x330781CB)},
        {0x330B64B8: ("swccu.dll", "?SetAtGrow@su_CDWordArray")},
    ),
}

REA = {
    "options_accessor": "ev_b3d8a433660b38bdac1be6e8759bf5a36c8dbc3d14101af833fc8b746ee53604",
    "edge_initializer": "ev_9fa3f7e73224c66d4768f0254db25131e28dc972a808e4420c6a28d0a24d4d71",
    "ordinary_export": "ev_69f4393215bf18c580bc4787ae648e2cb5092b0803811aa54eef174b872c729d",
    "kernel_options_routing": "ev_3000e5dcea6c9f7af2aeb5a4571043f6d69715027cad8278e80abd926bdefc75",
    "six_slots_from_computed_options": "ev_443a3a656188f56de6ced8913378ab58b44bd361cf41ae24fe602052369278cb",
}


def inspect(directory):
    rows = {}
    for name, (sha, ranges, links) in MODULES.items():
        path = (directory / name).resolve(strict=True)
        if path.is_relative_to(ROOT):
            raise ValueError("licensed original must stay outside the research checkout")
        image = PeImage(path)
        if image.sha256 != sha:
            raise ValueError("exact SOLIDWORKS 2026 image differs " + name)
        typed_imports = {}
        for address, (module, function) in links.items():
            target = image.imports()[address]
            if target["module"].casefold() != module.casefold() or not target["name"].startswith(function):
                raise ValueError("saved-options import identity differs")
            typed_imports[hex(address)] = {"module": target["module"], "export": function}
        rows[name] = {"sha256": sha, "image_bytes": len(image.data), "preferred_base": hex(image.base),
                      "roles": [image.pin(role, start, stop) for role, (start, stop) in ranges.items()],
                      "typed_imports": typed_imports}
    return {"schema": "kit.sw2026.chamfer-saved-options-source.v1", "build": "34.5.2.0604",
            "images": rows, "rea_evidence": REA,
            "fresh_array_branch": "present typed array of zero words, skip retained overrides and capture six after success",
            "native_processes": 0, "cad_documents_read": 0}


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--licensed-directory", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    with args.output.open("x", encoding="utf-8") as sink:
        json.dump(inspect(args.licensed_directory), sink, indent=2, sort_keys=True)
        sink.write("\n")
