from struct import pack

from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import (
    SelfFileInput,
)
from convert.adapters.solidworks.Archive.Construction.Header.HeaderInput import (
    HeaderInput,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


CASES = {
    "straight": {
        "name": "Trial A",
        "configuration": "Stock A",
        "description": "",
        "comment": "Initial",
        "alternate": "",
        "author": "Kit",
        "company": "",
        "revision": "Model created",
        "created": 1794600000,
        "modified": 1794600027,
        "updated": 1794600013,
        "saved": 1794600032,
        "root_id": 4,
        "reserved": (5,),
        "feature_ids": (6, 7),
        "config_id": 0,
        "config_stamp": 125,
        "geometry_stamp": 167,
        "status": 0,
        "validation": 0,
        "rebuild": 0,
        "flags": 256,
        "load_state": 0,
        "sort": 2,
    },
    "unicode": {
        "name": "Pièce β",
        "configuration": "設計 Ω",
        "description": "Ébauche",
        "comment": "変更 é",
        "alternate": "Variante",
        "author": "Author λ",
        "company": "Atelier É",
        "revision": "Révision α",
        "created": 1794900000,
        "modified": 1794900011,
        "updated": 1794900023,
        "saved": 1794900037,
        "root_id": 19,
        "reserved": (20, 21),
        "feature_ids": (22, 23),
        "config_id": 3,
        "config_stamp": 4000000012,
        "geometry_stamp": 3000000000,
        "status": 8,
        "validation": 0,
        "rebuild": 1,
        "flags": -3,
        "load_state": 7,
        "sort": -21,
    },
}


def native_node(name, fields, schema=1):
    return ArchiveNode(RuntimeClass(name, schema), fields)


def node_name(text):
    return native_node("moNodeName_c", {"f08": text})


def locator(case):
    return "C:\\KitSdkCandidates\\" + case["name"] + ".SLDPRT"


def build_inputs(case):
    root = native_node("moPart_c", {
        "f18": node_name(case["name"]),
        "f1300": case["geometry_stamp"],
    })
    allocator = PersistentIds(case["root_id"], case["reserved"])
    assert allocator.AllocateMut(root) == case["root_id"]
    for class_name, expected in zip(
        ("moProfileFeature_c", "moExtrusion_c"), case["feature_ids"], strict=True
    ):
        assert allocator.AllocateMut(native_node(class_name, {"owner": root})) == expected
    config = native_node("moPartConfiguration_c", {
        "owner": root,
        "f18": node_name(case["configuration"]),
        "f08": case["config_id"],
        "f860": case["config_stamp"],
        "f1f8": case["description"],
        "f4a8": case["comment"],
        "f498": case["alternate"],
        "f968": case["validation"],
        "f0c": case["status"],
        "f4c4": case["flags"],
        "fbd0": case["load_state"],
        "f6a0": None,
        "f2f0": None,
    })
    manager = native_node("moConfigurationMgr_c", {
        "owner": root,
        "f40c": 1,
        "f370": {"n": 1, "items": [{"o": config}]},
        "f360": config,
        "f368": config,
        "f75c": case["sort"],
    })
    header = HeaderInput(
        case["author"], case["company"], case["revision"],
        case["created"], case["modified"], case["updated"],
    )
    return root, manager, header, SelfFileInput(locator(case), case["saved"]), allocator


def descriptor(name, schema=1):
    name = name.encode("ascii")
    return pack("<3H", 0xFFFF, schema, len(name)) + name


def unicode_text(text):
    encoded = text.encode("utf-16-le")
    return pack("<BHB", 0xFF, 0xFFFE, len(encoded) // 2) + encoded


def header_attribution(case):
    return (
        descriptor("su_CStringArray", 0)
        + pack("<H", 1)
        + unicode_text(case["author"])
        + pack("<HH", 0x8003, 1)
        + unicode_text(case["company"])
        + descriptor("suObList")
        + pack("<H", 1)
        + descriptor("moLogs_c")
        + pack("<H", 1)
        + descriptor("moStamp_c")
        + pack("<HHHI", 0, 0, 0, case["created"])
        + unicode_text(case["revision"])
        + pack("<i", case["root_id"])
        + unicode_text(case["name"])
    )


def self_file(case):
    return (
        descriptor("moExtObject_c")
        + descriptor("moCStringHandle_c")
        + unicode_text(locator(case))
        + pack("<H", 0x800E)
        + unicode_text(case["name"])
        + pack("<HBI", 2, 0, case["created"])
        + unicode_text("") * 3
        + pack("<BBIiii", 0, 0, case["saved"], 1, 0, -1)
        + unicode_text(case["configuration"])
        + pack("<iiIi", case["config_id"], 0, 0, 0)
    )


def header_record(case, role):
    return (
        descriptor("moHeader_c")
        + pack("<i", role)
        + header_attribution(case)
        + pack("<IiHI", case["modified"], case["feature_ids"][-1] + 1, 0, 101)
        + self_file(case)
        + pack("<IiiIiiiH", 101, 0, 0, case["created"], 0, 0, 0, 0)
        + pack("<iIIHiiI", 0, 0, case["updated"], 0, 0, 0, 0)
        + pack("<iiiI", -1, -1, -1, 0)
        + bytes(64)
    )


def directory_record(case):
    return (
        descriptor("dmConfigMgrHeader_c")
        + pack("<H", 1)
        + descriptor("dmConfigHeader_c")
        + pack("<i", 1)
        + unicode_text(case["configuration"])
        + pack("<iI", case["config_id"], case["config_stamp"])
        + unicode_text(case["description"] or case["configuration"])
        + pack("<ii", -1, case["rebuild"])
        + unicode_text(case["comment"])
        + unicode_text(case["alternate"])
        + pack("<iiII", case["flags"], case["load_state"], case["geometry_stamp"], 101)
        + pack("<Ii", case["saved"], case["sort"])
    )
