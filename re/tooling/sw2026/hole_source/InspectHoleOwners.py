from argparse import ArgumentParser
from collections import Counter
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from struct import unpack_from
import json
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(ROOT / "re/automation"), str(HERE.parent.parent / "materials"), str(ROOT / "src")]

from Corpus import git, read_tree
from MaterialPe import PeImage
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Native import ParseXml

ANCHOR = "cd20b8ea0c17ee29d48e1ee767f836be8e0fe4f5"
MAP_SHA = "dbb788346ee44610cb365a44e6150a8264b03f93fed9832a19caa8ad24dabec4"
PE_SHA = "569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e"
RESOLVED = "Contents/Config-0-ResolvedFeatures"
FEATURES = ("moHoleWzd_c", "moSketchHole", "moAdvHoleWzd_c", "moHoleSeries_c")
CLASSES = (*FEATURES, "moBaseHoleWzd_c", "moHoleWizardInfo_c")
ACCESSORS = (
    ("moBaseHoleWzd_c", "getCenterLocSketch", 0x4B3C9AD0, 0),
    ("moBaseHoleWzd_c", "getSectionProfSketch", 0x4B3CA2A0, 0),
    ("moHoleWzd_c", "getCenterLocProfile", 0x4BF49F60, 15),
    ("moHoleWzd_c", "getHoleProfile", 0x4BF88420, 15),
    ("moHoleWzd_c", "getExitType", 0x4B2BCEB0, 7),
    ("moHoleWzd_c", "setHoleType", 0x4B291F00, 7),
    ("moHoleWzd_c", "getDiameterDepth", 0x4BF85E80, 0),
    ("moHoleWzd_c", "GetThruHoleDiameter", 0x4BF73D20, 0),
    ("moHoleWzd_c", "GetCounterBoreDiameter", 0x4BF71B90, 0),
    ("moHoleWzd_c", "GetCounterBoreDepth", 0x4BF71A40, 0),
    ("moHoleWzd_c", "GetCounterBoreDepthWithHC", 0x4BF71AA0, 0),
    ("moHoleWizardInfo_c", "getHoleTypeInfo", 0x4B28D350, 7),
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(raw):
    return sha256(raw).hexdigest()


def serializer(image, name, row):
    table = int(row["vtable"], 16)
    slot = table + 0x28
    target = image.u64(image.offset(slot))
    bounds = image.range(target)
    require(bounds and bounds[0] == target == int(row["serialize_addr"], 16),
            "actual serializer dispatch differs: " + name)
    locator = image.u64(image.offset(table - 8))
    signature, offset, _, desc, hierarchy, rel = unpack_from("<6I", image.data, image.offset(locator))
    require(signature == 1 and offset == 0 and image.base + rel == locator
            and image.string(image.base + desc + 16) == ".?AV" + name + "@@", "unbound RTTI owner: " + name)
    _, _, count, array = unpack_from("<4I", image.data, image.offset(image.base + hierarchy))
    require(0 < count <= 32, "invalid RTTI base count")
    lineage = []
    for index in range(count):
        item = image.u32(image.offset(image.base + array + index * 4))
        type_desc = image.u32(image.offset(image.base + item))
        text = image.string(image.base + type_desc + 16)
        require(text.startswith(".?AV") and text.endswith("@@"), "unexpected RTTI base type")
        lineage.append(text[4:-2])
    return {"vtable": hex(table), "virtual_cell": image.pin("Serialize cell", slot, slot + 8),
            "lineage": lineage, "body": image.pin(name + "::Serialize", *bounds)}


def native_owners(path):
    path = path.resolve(strict=True)
    require(path.name.casefold() == "sldmodu.dll" and not path.is_relative_to(ROOT),
            "provide the original model DLL outside the checkout")
    image = PeImage(path)
    require(image.base == 0x4B140000 and image.sha256 == PE_SHA, "model DLL is outside pinned SP05.2")
    data = git(ROOT, "show", ANCHOR + ":re/data/Serialization/SerializeMap2026.json")
    require(digest(data) == MAP_SHA, "current serializer inventory changed")
    mapping = json.loads(data)
    classes = {name: serializer(image, name, mapping[name]) for name in CLASSES}
    table = int(classes["moHoleWzd_c"]["vtable"], 16)
    dispatch = {hex(field): hex(image.u64(image.offset(table + field)))
                for field in (0x1A58, 0x2660, 0x2668, 0x2740)}
    exports = image.exports()
    accessors = {}
    for owner, name, start, leaf_length in ACCESSORS:
        (export,) = (row for row in exports if row["name"].startswith("?" + name + "@" + owner + "@@"))
        require(int(export["address"], 16) == start and export["forwarder"] is None, "unbound export: " + name)
        bounds = image.range(start) if not leaf_length else (start, start + leaf_length)
        require(bounds and bounds[0] == start, "unbound function bounds: " + name)
        accessors[name] = image.pin(owner + "::" + name, *bounds)
    base_calls = {}
    for address, target in ((0x4BB1381D, 0x4B3C92C0), (0x4B3C92E1, 0x4BB0D460), (0x4BB1F3A1, 0x4BB11640)):
        offset = image.offset(address)
        op, delta = unpack_from("<Bi", image.data, offset)
        require(op == 0xE8 and address + 5 + delta == target, "inherited serialize call differs")
        base_calls[hex(address)] = hex(target)
    return {"model_dll_sha256": image.sha256, "preferred_base": hex(image.base),
            "map_sha256": MAP_SHA, "classes": classes, "ordinary_dispatch": dispatch,
            "accessors": accessors, "inherited_serialize_calls": base_calls}


def keyword_role(element):
    roles = {"holewizard", "holewzd", "sketchhole", "advholewzd", "holeseries", "hole"}
    return any("".join(char for char in value.casefold() if char.isalpha()) in roles
               for value in (element.tag, element.get("Type", "")))


def descriptors(payload, name):
    token = name.encode("ascii")
    cursor = 0
    while (offset := payload.find(token, cursor)) >= 0:
        cursor = offset + len(token)
        if offset >= 6:
            marker, schema, length = unpack_from("<HHH", payload, offset - 6)
            if marker == 0xFFFF and length == len(token):
                yield {"offset": offset - 6, "schema": schema, "class": name}


def sources():
    entries = tuple((path, oid) for path, oid in read_tree(ROOT, ANCHOR).items()
                    if path.startswith("re/solidworks/") and path.casefold().endswith(".sldprt"))
    loaded = git(ROOT, "cat-file", "--batch", input_data=b"".join(oid.encode() + b"\n" for _, oid in entries))
    versions, hits, keywords, unknown = Counter(), Counter(), Counter(), Counter()
    resolved = Counter()
    manifest = sha256()
    legacy = None
    with BytesIO(loaded) as blobs:
        for path, oid in entries:
            actual, kind, size = blobs.readline().split()
            raw = blobs.read(int(size))
            require((actual.decode(), kind, len(raw), blobs.read(1)) == (oid, b"blob", int(size), b"\n"),
                    "invalid pinned Git blob framing")
            pin = digest(raw)
            manifest.update(json.dumps((path, pin), ensure_ascii=True, separators=(",", ":")).encode() + b"\n")
            archive = SldprtArchive.from_bytes(raw)
            version = str(ContainerMo(archive.streams))
            versions[version] += 1
            rows = [(name, match) for name, data in archive.streams.items() for cls in FEATURES
                    for match in descriptors(data, cls)]
            for cls in {match["class"] for _, match in rows}:
                hits[(version, cls)] += 1
            for cls in {match["class"] for name, match in rows if name == RESOLVED}:
                resolved[(version, cls)] += 1
            key_data = archive.get("swXmlContents/KeyWords")
            try:
                key = ParseXml(key_data) if key_data is not None else None
            except (ValueError, SyntaxError):
                key = None
            if key is None:
                unknown[version] += 1
            elif any(keyword_role(element) for element in key.iter()):
                keywords[version] += 1
            if oid == "a4e7f529a03cfd70eb3d5af493055058d5aa8789":
                legacy = {"path": path, "git_blob": oid, "sha256": pin, "version": int(version),
                          "resolved_sha256": digest(archive.require(RESOLVED)),
                          "keyword_sha256": digest(key_data),
                          "resolved_descriptors": [match for name, match in rows if name == RESOLVED],
                          "keyword_ids": [element.get("id") for element in key.iter() if keyword_role(element)]}
        require(not blobs.read() and legacy is not None, "pinned legacy contrast or batch closure differs")
    return {"revision": ANCHOR, "part_count": len(entries), "version_counts": dict(versions),
            "input_manifest_sha256": manifest.hexdigest(),
            "descriptor_parts": {"/".join(key): value for key, value in hits.items()},
            "resolved_descriptor_parts": {"/".join(key): value for key, value in resolved.items()},
            "keyword_parts": dict(keywords), "missing_or_unsupported_keywords": dict(unknown),
            "legacy_contrast": legacy}


def main():
    parser = ArgumentParser()
    parser.add_argument("model_dll", type=Path)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--output", type=Path)
    modes.add_argument("--check", type=Path)
    args = parser.parse_args()
    receipt = {"schema": "kit.sw2026.hole-archive-ownership.v1", "build": "34.5.2.0604",
               "pinned_pe": native_owners(args.model_dll), "tracked_sources": sources(),
               "native_processes": 0, "qualified_current_sources": 0, "heldout_oracle_inputs_read": 0,
               "writer_outputs": 0, "conversion_credit": 0}
    data = (json.dumps(receipt, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    if args.check:
        require(args.check.read_bytes() == data, "hole archive ownership receipt differs")
    else:
        with args.output.open("xb") as stream:
            stream.write(data)
    print(json.dumps({"sha256": digest(data), "tracked_sources": receipt["tracked_sources"]["part_count"],
                      "native_processes": 0}, sort_keys=True))


if __name__ == "__main__":
    main()
