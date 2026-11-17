from __future__ import annotations

from Core import ArchiveError, Obj
from Streams import StreamDoc, store_rooted
from builders.Metadata import FILE_VERSION, integer
from builders.Model import object_list


CONFIGURATION_MANAGER_HEADER = "Contents/CMgrHdr2"
PART_TRANSFORM_STAMP = 101


def _cstring(value: str, name: str) -> str:
    if type(value) is not str or "\x00" in value:
        raise ValueError(f"{name} must be text without null characters")
    return value


def _signed_dword(value: int, name: str) -> int:
    value = integer(value, name)
    return value if value < 0x80000000 else value - 0x100000000


def configuration_manager_header(*, manager: Obj, saved_at: int) -> Obj:
    if not isinstance(manager, Obj) or manager.cls != "moConfigurationMgr_c":
        raise ArchiveError("a configuration header requires the actual configuration manager")
    owner = manager["owner"]
    if not isinstance(owner, Obj) or owner.cls != "moPart_c":
        raise ArchiveError("configuration header construction requires an ordinary part")
    rows = manager["f370"]["items"]
    if len(rows) != 1 or manager["f370"]["n"] != len(rows) or manager["f40c"] != len(rows):
        raise ArchiveError("configuration header construction requires one configuration")
    configuration = rows[0]["o"]
    if not isinstance(configuration, Obj) or configuration.cls != "moPartConfiguration_c" or configuration["owner"] is not owner:
        raise ArchiveError("the configuration must belong to the managed part")
    if configuration is not manager["f360"] or configuration is not manager["f368"] or configuration["f6a0"] is not None:
        raise ArchiveError("configuration header construction requires an independent active configuration")
    if configuration.get("fbe0", 0) or configuration.get("fbf0", 0) or configuration["f2f0"] is not None:
        raise ArchiveError("excluded configurations and feature-comment sidecars require separate construction")

    name_node = configuration["f18"]
    if not isinstance(name_node, Obj) or name_node.cls != "moNodeName_c":
        raise ArchiveError("the configuration must have a native name object")
    name = _cstring(name_node["f08"], "configuration name")
    if not name:
        raise ValueError("configuration name must be nonempty")
    description = _cstring(configuration["f1f8"], "configuration description")
    node_flags = integer(configuration["f0c"], "configuration node flags")
    rebuild_state = integer(configuration["f968"], "configuration rebuild state", high=0xFF)
    entry = Obj("dmConfigHeader_c", {
        "f08": int(configuration is manager["f368"]),
        "f10": name,
        "f30": integer(configuration["f08"], "configuration id", high=0x7FFFFFFF),
        "f38": integer(configuration["f860"], "configuration update stamp"),
        "f18": description or name,
        "f34": -1,
        "f40": int(rebuild_state != 1 and bool(node_flags & 8)),
        "f20": _cstring(configuration["f4a8"], "configuration comment"),
        "f28": _cstring(configuration["f498"], "configuration alternate name"),
        "f44": _signed_dword(configuration["f4c4"], "configuration flags"),
        "f48": integer(configuration["fbd0"], "configuration ldr-dl state", low=-0x80000000, high=0x7FFFFFFF),
        "f50": integer(owner["f1300"], "part geometry stamp"),
        "f4c": PART_TRANSFORM_STAMP,
    })
    return Obj("dmConfigMgrHeader_c", {
        "f08": object_list((entry,)),
        "f60": integer(saved_at, "configuration manager save event"),
        "f68": _signed_dword(manager["f75c"], "configuration tree sort order"),
    })


def configuration_manager_header_stream(*, registry, header: Obj) -> bytes:
    if not isinstance(header, Obj) or header.cls != "dmConfigMgrHeader_c":
        raise ArchiveError("the configuration manager header stream requires its native root")
    document = StreamDoc(CONFIGURATION_MANAGER_HEADER, {"base": 1}, [header])
    return store_rooted(document, registry, FILE_VERSION)
