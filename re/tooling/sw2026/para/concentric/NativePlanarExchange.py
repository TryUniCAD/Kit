from hashlib import sha256
from struct import unpack

from InspectPartEnvironmentSource import Image


MODULE = "569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e"
WINDOWS = {
    "moMate::to_msgpack": (0x4BC80360, 0x4BC80536, "9b84e98f890d2988e4f94221f10e64647352d8edf5457143842c48d9bfd35c6a"),
    "moMateDim_c::to_msgpack": (0x4BC80650, 0x4BC8075C, "dc0d6ece8dee4cb5dc1edd011deaed8083c17b1983b8185876cadb97aacf2d2f"),
    "moMateDistanceDim_c::to_msgpack": (0x4BC80760, 0x4BC8087C, "87d8d6c74809c63471f706079dd80978746ced0a5a7c03733e3234553dad9add"),
    "moMateNGeoms_c::to_msgpack": (0x4BC80B00, 0x4BC80FF6, "66ca728ea705034f8777d57342914324a8030c7300ed966e48d804f953a512f0"),
    "moCompFeature_c::to_msgpack": (0x4B809C20, 0x4B809E30, "0b572453891c0be4ebe8a865f20fd1d740a75af99c197a1a08239e116ff46b1d"),
    "distance_value": (0x4BC568B0, 0x4BC568E1, "2b0707182b00772822b7b696ecb3a95e29d3a9193bd949c4d7e5c1642b27d467"),
    "moDisplayDim::getValue": (0x4C888D40, 0x4C888E92, "8337a1dc5b0bfeffd58b8855ecafdccdb1513ce27f22f7026c7798d2bd4b2ec6"),
    "moDimHandle_c::getValue": (0x4C844D80, 0x4C844DC2, "e327ff72feddb0609c15f14b6bdf7056add9eea087c856c2fb252e95c74f379f"),
    "distance_base_constructor": (0x4BC2D820, 0x4BC2D896, "c6a2a804727daf0a9e02bd5d486afc809a5b25d0dbb97ef66606c9909d3624e0"),
    "moMateDim_c::Serialize": (0x4B669510, 0x4B669686, "37503719e91209aa49f9c4df82f05b2862e8b485ce79563f13f65914e4031af3"),
    "moMateDistanceDim_c::Serialize": (0x4B669690, 0x4B669831, "a1d650f009ff7e707be7a22539d0e7e17e05ecdf6dd233ea94f633369383c22a"),
}
TABLES = {
    "moMateCoincident": (0x4CFA46E0, 0x4D338348, {0x30: 0x4BC80B00}),
    "moMateDistanceDim_c": (0x4CFAFD18, 0x4D339040, {0x30: 0x4BC80760, 0x23C0: 0x4BC568B0}),
    "moDisplayDistanceDim_c": (0x4D253270, 0x4D3738C0, {0x868: 0x4C888D40}),
    "moCompRefPlane_c": (0x4CD8D220, 0x4D2EB278, {0x30: 0x4B809C20}),
}
KEYS = {
    0x4CFDEB10: "Aligment",
    0x4CFDEB20: "NumberEntities",
    0x4CFDEB40: "FlipDim",
    0x4CFDEB48: "Distance",
    0x4CE96480: "featureID",
}


def native_planar_exchange(path):
    image = Image(path, MODULE)
    spans = {}
    for name, (start, end, expected) in WINDOWS.items():
        digest = sha256(image.read(start, end)).hexdigest()
        if digest != expected or not any((image.base + first, image.base + last) == (start, end)
                                         for first, last, _ in image.functions):
            raise ValueError("native exchange serializer window changed: " + name)
        spans[name] = {"start": hex(start), "end_exclusive": hex(end), "sha256": digest}
    for start, name in KEYS.items():
        text = name.encode("ascii") + b"\0"
        if image.read(start, start + len(text)) != text:
            raise ValueError("native exchange key changed: " + name)
    tables = {}
    for name, (table, locator, slots) in TABLES.items():
        if unpack("<Q", image.read(table - 8, table))[0] != locator:
            raise ValueError("native exchange virtual table lost its type descriptor")
        signature, offset, _, type_rva, _, self_rva = unpack("<IIIIII", image.read(locator, locator + 24))
        start = image.base + type_rva + 16
        text = b".?AV" + name.encode("ascii") + b"@@\0"
        if (signature, offset, image.base + self_rva) != (1, 0, locator) or image.read(start, start + len(text)) != text:
            raise ValueError("native exchange RTTI changed: " + name)
        values = {}
        for slot, target in slots.items():
            cell = table + slot
            if unpack("<Q", image.read(cell, cell + 8))[0] != target:
                raise ValueError("native exchange virtual target changed: " + name)
            values[hex(slot)] = {"cell": hex(cell), "target": hex(target)}
        tables[name] = {"complete_object_locator": hex(locator), "slots": values}
    return {"application_build": "34.5.2.0604", "module_sha256": MODULE, "functions": spans,
            "tables": tables, "keys": {name: hex(address) for address, name in KEYS.items()}}
