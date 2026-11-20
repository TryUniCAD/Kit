from argparse import ArgumentParser
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
from struct import pack, unpack_from
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "src"), str(Path(__file__).resolve().parent)]

from MakeHeadAliasCase import DIRECTORY, PATH, SELF, authored_lanes, frame_lanes
from convert.adapters.solidworks.Archive.Config.Link.ReadPartStart import ReadPartStart
from convert.adapters.solidworks.Archive.Header.ReadFileTable import GetFileRef
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Maps.FindObject import FindObject
from convert.adapters.solidworks.Archive.Maps.ObjectIndex import ObjectIndex
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive, SldprtFormatError

CONFIG = "Contents/Config-0"
MODEL = "Contents/Config-0-ModelHeader"
STANDALONE = "Header2"
TRACKED = ("ladder", "concave")
CASES = {
    "ladder": (
        "re/solidworks/v2026/corpus/ladder/L1_boss.SLDPRT",
        "55e5a9840cc78a1d4b3ac4b8de3f37540695494e4d7a0edfb3cd3a2a876e2ac6",
        "e7e700d5b112e7d9d1b1297bac8149707e67d9aac2e3c6f890b4cb2f97b1e5b2",
        "9e3d68bd031e4797a2f05504cf8962e5e3a337d2816ec963194165371d5b4659",
        "9e3d68bd031e4797a2f05504cf8962e5e3a337d2816ec963194165371d5b4659",
        "f73c4aef96c343796797ec2d05d2309eb8535ad1cd8d0add127ef78bbe1c2d48",
        3052,
        69,
        "Part1",
        "Default",
    ),
    "concave": (
        "re/solidworks/v2026/corpus/local-import-readback/ConcaveOwned.SLDPRT",
        "fa1b84b7cd9e8860d549c599fdb536c6de965e3ec7b4ed5f53706cb57c743d33",
        "f8b42cb72d75f14be04410c18daae6f77164e2561dd5e99d7f26a107b5b049a1",
        "f4cce850be7777c5f6aad10d0bc46bda2e60448fac1ca4cde309df56063516aa",
        "0d8551d418c050d4f3d737edac10225af00146037f6eefa2b60511b8db4ad53d",
        "e980ccad98c6d452f498a58c9a76a3ec5e83060ac8543c04137cf3a0a1947ce0",
        2105,
        15,
        "ConcaveOwned",
        "Default",
    ),
    "circle": (
        "PartPropertySource01/Inspection/CircularPropertiesAuthor/CircularProperties.SLDPRT",
        "1c1bc718661b88a119bc3ac041f97d56cf5b4a06e290e1ac1afc79d423e42d23",
        "5c78942508f55177db00ea7f394856a6d8c72683b19163b4e3d14e557fe045c7",
        "dbff4fc3e0c22cc292d30541648df2aef7e7e193c513d005ceb3cbc88e962a9a",
        "dbff4fc3e0c22cc292d30541648df2aef7e7e193c513d005ceb3cbc88e962a9a",
        "277cd89e2f0099a102379a1c773135997325f5e9580baf3465ad91f7f748de9e",
        3058,
        25,
        "CircularInput",
        "modeled default",
    ),
    "rectangle": (
        "PartPropertySource01/Inspection/RectanglePropertiesAuthor/RectangleProperties.SLDPRT",
        "4377bf5680f30d1c9de52227928911e55604a75d30ceb987240df00d6b1b1805",
        "a77890c040efaa9792d0b151c5d38c8b9458301781c399a4a52b9b4a9d003d3a",
        "c3fd32646c92282433f0d265e0ee767256f869489c88efc0bdf41b925b9c058b",
        "c3fd32646c92282433f0d265e0ee767256f869489c88efc0bdf41b925b9c058b",
        "2f9067bb0518f546083ee2d5491c0bd6cf530fdf75658ffb68bcd15c23993895",
        3070,
        70,
        "RectangleInput",
        "Default",
    ),
    "polygon_saved": (
        "SdkPartPropertiesNative02/Inspection/polygonEdit/PropertyPolygonDiscoveryEdited.SLDPRT",
        "e311ba0626114291e62aacd26f705c8d304baa5d0315f89972fdde66bdee1f14",
        "0c18e5880e64c1ff1fef5560cd16e2b57c94a2545ad8ee73371ac79cc0bec631",
        "42523f3d74f6ec041b06f5b3012c178627c626c82a9ac3d13faf492848906487",
        "42523f3d74f6ec041b06f5b3012c178627c626c82a9ac3d13faf492848906487",
        "81c9fd0dc8ad5e73e211fd6cee48623fcd34dbaf80dab51776a6a57703112ae8",
        3080,
        25,
        "PropertyPolygonDiscovery",
        "modeled default",
    ),
    "circle_saved": (
        "SdkPartPropertiesNative02/Inspection/circleEdit/PropertyCircleDiscoveryEdited.SLDPRT",
        "8007d21df3db5fc58c23d3fe589cfc15cf274ac83d9b2daa4878ee792e104e30",
        "94e7079c568be9d3b6adf5b16215cf23d668f5f8dafe86462df218da86f9a8b4",
        "beed1d3222c13d77d850506edb98607c272ffe5943b39929e1f2babe15b53f3d",
        "beed1d3222c13d77d850506edb98607c272ffe5943b39929e1f2babe15b53f3d",
        "2dda18577f152322175a418e10cdfd4aac68b5343bdae407355b0908b2c4a30c",
        3078,
        25,
        "PropertyCircleDiscovery",
        "modeled default",
    ),
}


def digest(data):
    return sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def audit_run(event, _args):
    if event in ("open", "os.listdir", "os.scandir", "os.system", "os.exec",
                 "os.posix_spawn", "subprocess.Popen", "ctypes.dlopen") or event.startswith("socket."):
        raise PermissionError("the linked part start attempted external access")


def guard_runtime():
    for codec in ("ascii", "latin-1", "cp1252", "utf-16-le"):
        lookup(codec)
    sys.addaudithook(audit_run)


def replace_lane(archive, name, data):
    records = tuple(
        replace(record, data=data) if record.name == name else record
        for record in archive.records
        if record.name != name or data is not None
    )
    return replace(archive, records=records)


def refuse(label, archive, expected, *, exact=False):
    try:
        ReadPartStart(archive)
    except (ValueError, SldprtFormatError) as error:
        detail = str(error)
        require(detail == expected if exact else expected in detail,
                f"{label} failed at a different boundary: {detail}")
        return label
    raise ValueError(f"{label} crossed the named part start boundary")


def authored_faults(archive, config, model, section):
    another_class = b"moAssembly_c"
    wrong_root = pack("<3H", 0xFFFF, 1, len(another_class)) + another_class + config[section:]
    return [
        refuse("missing_model_header", replace_lane(archive, MODEL, None), "required stream is missing: " + MODEL),
        refuse("malformed_model_header", replace_lane(archive, MODEL, b"\x01"), "no complete unsigned short"),
        refuse("header_tail", replace_lane(archive, MODEL, model + b"\0"), "header has an incomplete root or trailing data"),
        refuse("missing_configuration", replace_lane(archive, CONFIG, None), "required stream is missing: " + CONFIG),
        refuse("one_byte_configuration", replace_lane(archive, CONFIG, b"\x01"), "no complete unsigned short"),
        refuse("null_root", replace_lane(archive, CONFIG, b"\0\0" + config[2:]), "requires a current part"),
        refuse("other_root", replace_lane(archive, CONFIG, wrong_root), "requires a current part"),
        refuse("other_root_schema", replace_lane(archive, CONFIG, config[:2] + pack("<H", 0) + config[4:]), "requires a current part"),
        refuse("truncated_light_header", replace_lane(archive, CONFIG, config[:section + 3]), "truncated SOLIDWORKS archive field"),
        refuse("small_light_frame", replace_lane(archive, CONFIG, config[:section] + pack("<I", 7) + config[section + 4:]), "lightweight section is unbounded"),
        refuse("oversized_light_frame", replace_lane(archive, CONFIG, config[:section] + pack("<I", len(config)) + config[section + 4:]), "lightweight section is unbounded"),
        refuse("other_container_version", replace(archive, format_version=3), "requires format 4 at version 19000"),
    ]


def directory_order(archive, original_header):
    linked = ReadPartStart(archive)
    fields = linked.HeaderValue.FieldsValue
    self_file, directory = fields["f38"], fields["f30"]
    aliases = (self_file, *directory.FieldsValue["items"])
    source_indices = [node.IndexValue for node in aliases]
    require(source_indices == [12, 6, 10], "standalone header allocation order changed")
    identities = []
    for node in aliases:
        ref = GetFileRef(node)
        require(ref.PathValue == PATH and ref.KindValue == 2, "authored file identity changed")
        identities.append((ref.NameValue, ref.ConfigValue, node.FieldsValue["f48"]))
    require(identities == [SELF, *DIRECTORY], "authored header directory order changed")
    handles = [node.FieldsValue["shared"]["h18"] for node in aliases]
    require(all(handle is handles[0] for handle in handles), "shared path handle lost identity")
    root = linked.RootValue
    entries = linked.MapValue.EntriesValue
    slots = [entry.IndexValue for entry in entries]
    require(slots == [1, 2, 3, 4, 5] and entries[0].EntryValue is root.ClassValue
            and entries[1].EntryValue is root and not root.FieldsValue and root.EndOffset is None,
            "configuration root prefix allocation changed")
    require((linked.LightOffset, linked.LightSize, linked.BaseValue, linked.MapValue.CounterValue) ==
            (18, 8, 6, 6), "directory aliases changed the bounded cursor or map handoff")
    maps = ArchiveMaps(linked.BaseValue, linked.MapValue)
    for slot, node in zip(slots[2:], aliases, strict=True):
        require(FindObject(maps, slot) is node and ObjectIndex(maps, node) == slot,
                "configuration slot did not resolve the original ordered header node")
    require(WriteHeadGraph(linked.HeaderValue, 19000) == original_header
            and [node.IndexValue for node in aliases] == source_indices,
            "linking changed standalone header bytes or object indices")
    return {
        "aliases": identities,
        "source_indices": source_indices,
        "config_slots": slots[2:],
        "lightweight_span": [linked.LightOffset, linked.LightOffset + linked.LightSize],
        "base": linked.BaseValue,
        "counter": linked.MapValue.CounterValue,
    }


def authored_case():
    guard_runtime()
    lanes = authored_lanes()
    current_raw = frame_lanes(lanes, 19000)
    older_raw = frame_lanes(lanes, 18900)
    current = SldprtArchive.from_bytes(current_raw)
    older = SldprtArchive.from_bytes(older_raw)
    require(current.format_version == older.format_version == 4 and current.file_id == older.file_id,
            "logical version case changed the physical container profile")
    require(ContainerMo(current.Streams) == 19000 and ContainerMo(older.Streams) == 18900,
            "physical version lanes did not select different logical versions")
    require(current.Streams == {**lanes, "_MO_VERSION_19000": b""}
            and older.Streams == {**lanes, "_MO_VERSION_18900": b""},
            "paired archive contents changed beyond the version marker")
    outcome = directory_order(current, lanes[MODEL])
    require(lanes[MODEL] != lanes[STANDALONE], "authored header decoy must differ")
    refusal = refuse("other_logical_version", older, "requires format 4 at version 19000")
    return {
        "case": "authored",
        **outcome,
        "physical_format": current.format_version,
        "logical_versions": [ContainerMo(current.Streams), ContainerMo(older.Streams)],
        "common_lane_sha256": {name: digest(data) for name, data in lanes.items()},
        "physical_archive_sha256": [digest(current_raw), digest(older_raw)],
        "refusals": [refusal],
        "runtime_external_accesses": 0,
    }


def version_order_case():
    guard_runtime()
    valid = authored_lanes()
    malformed_config = pack("<H", 0x7FFF)
    malformed_header = pack("<H", 0xFFFF)
    config_fault = {**valid, CONFIG: malformed_config}
    paired_fault = {**config_fault, MODEL: malformed_header}
    cases = (
        ("wrong_version", 18900, paired_fault,
         "SOLIDWORKS configuration start requires format 4 at version 19000"),
        ("current_bad_header", 19000, paired_fault, "truncated SOLIDWORKS archive field at 2"),
        ("current_bad_config", 19000, config_fault, "archive tag has no complete unsigned dword"),
    )
    results = []
    for label, version, lanes, expected in cases:
        raw = frame_lanes(lanes, version)
        archive = SldprtArchive.from_bytes(raw)
        require(archive.format_version == 4 and ContainerMo(archive.Streams) == version,
                "version-order container has the wrong physical or logical profile")
        require(archive.Streams == {**lanes, f"_MO_VERSION_{version}": b""},
                "version-order container changed the authored fault streams")
        results.append({
            "stage": refuse(label, archive, expected, exact=True),
            "diagnostic": expected,
            "physical_format": archive.format_version,
            "logical_version": version,
            "raw_archive_sha256": digest(raw),
            "required_lane_sha256": {name: digest(archive.require(name)) for name in (CONFIG, MODEL)},
        })
    return {
        "case": "version-order",
        "stages": results,
        "runtime_external_accesses": 0,
    }


def read_case(case, root):
    path, file_sha, config_sha, model_sha, standalone_sha, prefix_sha, end, native_idx, name, config_name = CASES[case]
    source = (root / path).read_bytes()
    require(digest(source) == file_sha, "unexpected part control hash")
    archive = SldprtArchive.from_bytes(source)
    model = archive.require(MODEL)
    config = archive.require(CONFIG)
    standalone = archive.require(STANDALONE)
    require((digest(config), digest(model), digest(standalone)) ==
            (config_sha, model_sha, standalone_sha), "wrong named stream roles")
    guard_runtime()
    ans = ReadPartStart(archive)
    root_node, header = ans.RootValue, ans.HeaderValue
    tag_word, schema, class_size = unpack_from("<3H", config)
    section = 6 + class_size
    class_name = config[6:section].decode("ascii")
    size = unpack_from("<I", config, section)[0]
    require(tag_word == 0xFFFF and (class_name, schema) == ("moPart_c", 1), "wrong wire root")
    require((ans.LightOffset, ans.LightSize) == (section + 4, size) and ans.LightOffset + size == end,
            "configuration prefix moved or disagrees with the native trace")
    require(digest(config[:ans.LightOffset]) == prefix_sha, "wrong prefix")
    require((root_node.IndexValue, root_node.StartOffset, root_node.EndOffset) == (2, 0, None)
            and not root_node.FieldsValue, "model start claimed a decoded body")
    one, two, three = ans.MapValue.EntriesValue
    source_file = header.FieldsValue["f38"]
    require(header.IndexValue == 2 and header.FieldsValue["f30"] is None and source_file.IndexValue == native_idx,
            "wrong original header identity")
    require((one.IndexValue, two.IndexValue, three.IndexValue) == (1, 2, 3)
            and one.EntryValue is root_node.ClassValue and two.EntryValue is root_node
            and three.EntryValue is source_file and (ans.BaseValue, ans.MapValue.CounterValue) == (4, 4),
            "configuration did not reserve the original identities")
    maps = ArchiveMaps(ans.BaseValue, ans.MapValue)
    require(FindObject(maps, 3) is source_file and ObjectIndex(maps, source_file) == 3,
            "inherited slot did not resolve through the actual object lookup")
    native_file = GetFileRef(source_file)
    require((native_file.NameValue, native_file.KindValue, native_file.ConfigValue) == (name, 2, config_name),
            "inherited file fields differ")
    rebuilt = WriteHeadGraph(header, 19000)
    require(rebuilt == model, "model header role or original graph fields changed")
    negatives = authored_faults(archive, config, model, section) if case == "concave" else []
    return {
        "case": case,
        "file_sha256": file_sha,
        "config_sha256": config_sha,
        "model_header_sha256": digest(rebuilt),
        "standalone_header_sha256": standalone_sha,
        "prefix_sha256": prefix_sha,
        "root": [class_name, schema, root_node.IndexValue],
        "lightweight_span": [ans.LightOffset, end],
        "model_words": list(unpack_from("<iI", config, ans.LightOffset)),
        "base": ans.BaseValue,
        "counter": ans.MapValue.CounterValue,
        "map_slots": [entry.IndexValue for entry in ans.MapValue.EntriesValue],
        "header_index": native_idx,
        "config_index": ObjectIndex(maps, source_file),
        "file_identity": [name, native_file.KindValue, config_name],
        "runtime_external_accesses": 0,
        "refusals": negatives,
    }


def main():
    parser = ArgumentParser(description="Verify the named ordinary part header alias handoff")
    parser.add_argument("case", choices=(*CASES, "authored", "version-order"))
    parser.add_argument("--disclosed-root", type=Path)
    args = parser.parse_args()
    if args.case == "authored":
        print(json.dumps(authored_case(), sort_keys=True))
        return
    if args.case == "version-order":
        print(json.dumps(version_order_case(), sort_keys=True))
        return
    if args.case not in TRACKED and args.disclosed_root is None:
        parser.error("the selected control requires its disclosed root")
    root = ROOT if args.case in TRACKED else args.disclosed_root
    print(json.dumps(read_case(args.case, root), sort_keys=True))


if __name__ == "__main__":
    main()
