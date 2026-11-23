from hashlib import sha256

from InspectPartEnvironmentSource import Image
from ProjectD01Concentric import require

MODULE_SHA256 = "569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e"
ORACLE_BUILD = "34.5.2.0604"

GETTERS = {
    "owner_present": (0x4B281410, "8b 41 10 c3"),
    "configuration_suppression": (0x4B282E20, "8b 41 20 c3"),
    "occurrence_id": (0x4B283BA0, "8b 41 08 c3"),
    "node_kind": (0x4B283C40, "8b 41 14 c3"),
    "length_unit": (0x4B2845D0, "8b 81 f4 00 00 00 c3"),
    "ordinary_configuration_flags": (0x4B284700, "8b 41 30 c3"),
    "mode_blank_assembly": (0x4B284700, "8b 41 30 c3"),
    "root_node_blank_assembly": (0x4B284D40, "8b 81 b0 00 00 00 c3"),
    "needs_rebuild": (0x4B285760, "8b 41 18 c3"),
    "node_visibility": (0x4B285F70, "8b 41 58 c3"),
    "unit_system": (0x4B286320, "8b 81 f8 00 00 00 c3"),
    "configuration_id": (0x4B289A60, "8b 41 2c c3"),
    "virtual_occurrence": (0x4B299710, "8b 41 5c c3"),
    "needs_update": (0x4B2A7540, "8b 41 1c c3"),
    "mass_unit": (0x4B2A7730, "8b 81 fc 00 00 00 c3"),
}
CLOCK_LANES = {
    "creation_time_store": (0x4B74270D, "48 89 57 10"),
    "update_time_from_header": (0x4B742713, "48 8b 43 48 48 89 47 18"),
    "update_stamp_store": (0x4B742721, "89 47 20"),
}
HEADER_IMPORTS = {
    "0x4cd35290": "?getCreationTime@moHeader_c@@",
    "0x4cd351a8": "?getCurrentUpdateStamp@moHeader_c@@",
    "0x4cd354b0": "?resetCreationTime@moHeader_c@@",
    "0x4cd354b8": "?setUpdateTimeStamp@moHeader_c@@",
    "0x4cd35280": "?setUpdateStamp@moHeader_c@@",
}


def verify_native_content(path):
    image = Image(path, MODULE_SHA256)
    imports = image.imports()
    for address, name in HEADER_IMPORTS.items():
        target = imports[address]
        require(
            target["module"].casefold() == "sldarchiveu.dll"
            and target["name"].startswith(name),
            "content-index header import changed",
        )
    anchors = {}
    for name, (address, encoded) in (GETTERS | CLOCK_LANES).items():
        expected = bytes.fromhex(encoded)
        value = image.read(address, address + len(expected))
        require(value == expected, "content-index member ownership changed: " + name)
        anchors[name] = {
            "va": hex(address),
            "bytes": len(value),
            "sha256": sha256(value).hexdigest(),
        }
    spans = []
    for start, end in ((0x4B7426E0, 0x4B742779), (0x4B73F690, 0x4B73F790)):
        spans.append(
            {
                "va": hex(start),
                "end_exclusive": hex(end),
                "sha256": sha256(image.read(start, end)).hexdigest(),
            }
        )
    return {
        "build": ORACLE_BUILD,
        "module_sha256": MODULE_SHA256,
        "instruction_anchors": anchors,
        "spans": spans,
        "header_imports": {address: imports[address] for address in HEADER_IMPORTS},
    }
