from struct import pack

from convert.adapters.solidworks.Archive.Config.Master.MasterLayout import KMasterClass
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


def text(value):
    payload = value.encode("utf-16-le")
    return pack("<BHB", 255, 65534, len(payload) // 2) + payload


def authored():
    wire = (
        pack("<HiIii", 0, -3, 26, -1, -19) + text("")
        + pack("<iHHi", 0, 0, 0, 0)
        + pack("<iiIB", -29, -31, 0xF0000004, 0)
        + pack("<iiiidiH", -37, 41, -43, 47, 0.25, -53, 0)
        + text("λ😀")
        + pack("<BHHBIHhf", 7, 11, 13, 17, 0xF0000009, 23, -31, 0.125)
        + pack("<iiHIBBiiiiiHiii", -59, 61, 0, 0xE0000013, 3, 2,
               -67, 71, -73, 79, -83, 89, -97, 101, 0)
    )
    fields = {
        "f18": None, "f0c": -3, "f28": 26, "f08": -1, "f2c": -19, "f20": "",
        "has_list68": 0, "f78": None, "f60": {"list": {"n": 0, "items": []}, "tail": 0},
        "f298": -29, "f28c": -31, "f29c": 0xF0000004, "has_f1e8": 0,
        "f2a8": -37, "f2b8": 41, "f2bc": -43, "f2b0": 47, "f1e0": 0.25,
        "f2b4": -53, "f258": None, "f1f8": "λ😀", "f1f4": 7,
        "f2c8": {"f00": 11, "f02": 13, "f04": 17, "f08": {
            "f00": 0xF0000009, "f04": 23, "f08": {"f06": -31, "f00": 0.125}
        }},
        "f2ec": -59, "fa8": 61, "f2f0": None, "f208": 0xE0000013, "f300": 3, "f301": 2,
        "f318": -67, "hidden": 71, "f30c": -73, "f2a4": 79, "f2a0": -83, "f98": 89,
        "f2ac": -97, "f344": 101, "f358": [],
    }
    return wire, ArchiveNode(KMasterClass, fields)
