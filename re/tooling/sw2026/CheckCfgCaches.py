from argparse import ArgumentParser
from codecs import lookup
from hashlib import sha256
import json
from pathlib import Path
from struct import pack, unpack
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from convert.adapters.solidworks.Archive.Config.Caches.ReadCfgCache import ReadCfgCache
from convert.adapters.solidworks.Archive.Header.HeaderRefNodes import HeaderRefNodes
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Maps.MapEntry import MapEntry
from convert.adapters.solidworks.Archive.Maps.MapSnapshot import MapSnapshot
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.ReadTypeDescMut import ReadTypeDescMut
from convert.adapters.solidworks.Archive.Tags.ReadTag import ReadTag
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive
from ReadWirePartCaches import author_mass_wire, read_mass_wire

EMPTY_HASH = "df3f619804a92fdb4057192dc43dd748ea778adc52bc498ce80524c014b81119"
NATIVE_CASES = {
    "ladder": (
        "re/solidworks/v2026/corpus/ladder/L1_boss.SLDPRT",
        "55e5a9840cc78a1d4b3ac4b8de3f37540695494e4d7a0edfb3cd3a2a876e2ac6",
        "e7e700d5b112e7d9d1b1297bac8149707e67d9aac2e3c6f890b4cb2f97b1e5b2",
        "9e3d68bd031e4797a2f05504cf8962e5e3a337d2816ec963194165371d5b4659",
        (25151, 25155, 108, EMPTY_HASH),
        (25370, 25374, 110, EMPTY_HASH),
    ),
    "concave": (
        "re/solidworks/v2026/corpus/local-import-readback/ConcaveOwned.SLDPRT",
        "fa1b84b7cd9e8860d549c599fdb536c6de965e3ec7b4ed5f53706cb57c743d33",
        "f8b42cb72d75f14be04410c18daae6f77164e2561dd5e99d7f26a107b5b049a1",
        "f4cce850be7777c5f6aad10d0bc46bda2e60448fac1ca4cde309df56063516aa",
        (22654, 22658, 94, EMPTY_HASH),
        (22680, 22684, 94, EMPTY_HASH),
    ),
}
DISCLOSED_CASES = {
    "circle": (
        "PartPropertySource01/Inspection/CircularPropertiesAuthor/CircularProperties.SLDPRT",
        "1c1bc718661b88a119bc3ac041f97d56cf5b4a06e290e1ac1afc79d423e42d23",
        "5c78942508f55177db00ea7f394856a6d8c72683b19163b4e3d14e557fe045c7",
        "dbff4fc3e0c22cc292d30541648df2aef7e7e193c513d005ceb3cbc88e962a9a",
        (25542, 25820, 120, "c746956086c2a50c590354c3bf0615f0c1cf31c1051e7c5b5e942ec6a385da95"),
        (26035, 26039, 122, EMPTY_HASH),
    ),
    "polygon": (
        "SdkPartPropertiesNative02/Inspection/polygonEdit/PropertyPolygonDiscoveryEdited.SLDPRT",
        "e311ba0626114291e62aacd26f705c8d304baa5d0315f89972fdde66bdee1f14",
        "0c18e5880e64c1ff1fef5560cd16e2b57c94a2545ad8ee73371ac79cc0bec631",
        "42523f3d74f6ec041b06f5b3012c178627c626c82a9ac3d13faf492848906487",
        (25564, 25850, 120, "2160148b4498dce04a212b87fc10490d124eeb6942b8913ed498ba95e9dee9bb"),
        (26065, 26069, 122, EMPTY_HASH),
    ),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return sha256(data).hexdigest()


def normalize(value):
    return json.dumps(value, sort_keys=True, allow_nan=False, separators=(",", ":"))


def context_entries(config, header, version):
    tag, offset = ReadTag(config, 0)
    require(tag.KindValue == "NewClass", "control part must declare its root")
    desc = ReadTypeDescMut(BinaryReader(config, offset))
    require((desc.NameValue, desc.SchemaValue) == ("moPart_c", 1), "control root is not an ordinary part")
    part = ArchiveNode(desc, {}, StartOffset=0, IndexValue=2)
    aliases = HeaderRefNodes(ReadHeaderGraph(header, version), version)
    require(len(aliases) == 1, "unexpected model-header alias profile")
    return part, (MapEntry(1, desc), MapEntry(2, part), MapEntry(3, aliases[0]))


def audit_run(event, _args):
    if event in ("open", "os.listdir", "os.scandir", "os.system", "os.exec",
                 "os.posix_spawn", "subprocess.Popen", "ctypes.dlopen") or event.startswith("socket."):
        raise PermissionError("the native cache reader attempted external access")


def guard_runtime():
    for codec in ("ascii", "utf-16-le", "latin-1", "cp1252"):
        lookup(codec)
    sys.addaudithook(audit_run)


def read_case(case, root):
    records = NATIVE_CASES if case in NATIVE_CASES else DISCLOSED_CASES
    relative, file_hash, config_hash, header_hash, mass, bounds = records[case]
    path = root / relative
    raw = path.read_bytes()
    require(digest(raw) == file_hash, "unexpected cache control bytes")
    archive = SldprtArchive.from_bytes(raw)
    version = ContainerMo(archive.streams)
    require(archive.format_version == 4 and version == 19000, "unsupported cache control")
    config = archive.require("Contents/Config-0")
    header = archive.require("Contents/Config-0-ModelHeader")
    require((digest(config), digest(header)) == (config_hash, header_hash), "unexpected configuration or header")
    part, entries = context_entries(config, header, version)
    guard_runtime()
    observed = {}
    for name, interval in (("mass", mass), ("bounds", bounds)):
        start, end, counter, expected = interval
        data = config[start:end]
        require(digest(data) == expected, "wrong cache interval")
        observed[name] = inspect(data, version, MapSnapshot(counter, entries), part, name)
    return {"case": case, "file_sha256": file_hash, "config_sha256": config_hash,
            "header_sha256": header_hash, "records": observed, "runtime_external_accesses": 0}


def inspect(data, version, seed, part, kind):
    result = ReadCfgCache(data, version, seed, part, kind)
    reference = read_mass_wire(data) if kind == "mass" else {"f1640": []}
    if kind == "bounds":
        require(unpack("<i", data) == (0,), "unexpected reference bounds count")
    fields = dict(result.FieldsValue)
    normalized = normalize(reference)
    require(normalize(fields) == normalized, "typed cache differs from independent wire fields")
    require(result.MapValue == seed and all(
        before is after for before, after in zip(
            seed.EntriesValue, result.MapValue.EntriesValue, strict=True,
        )
    ), "cache changed the parent map")
    require(part.FieldsValue == {}, "cache changed its part context")
    require(result.ReportValue["completed"], "cache not fully consumed")
    return {
        "bytes": len(data),
        "sha256": digest(data),
        "fields_sha256": digest(normalized.encode()),
        "fields": fields,
        "counter": result.MapValue.CounterValue,
        "anchor_slots": [entry.IndexValue for entry in seed.EntriesValue],
        "layouts": result.ReportValue["used_schemas"],
    }


def refuse(label, payload, seed, part, kind, expected, version=19000):
    try:
        ReadCfgCache(payload, version, seed, part, kind)
    except ValueError as error:
        require(expected in str(error), f"{label} failed at a different boundary: {error}")
        return label
    raise ValueError(f"{label} crossed the scope boundary")


def authored():
    native = NATIVE_CASES["ladder"]
    raw = (ROOT / native[0]).read_bytes()
    require(digest(raw) == native[1], "wrong authored context control")
    archive = SldprtArchive.from_bytes(raw)
    config = archive.require("Contents/Config-0")
    header = archive.require("Contents/Config-0-ModelHeader")
    require((digest(config), digest(header)) == native[2:4], "wrong authored context lanes")
    part, entries = context_entries(config, header, 19000)
    seed = MapSnapshot(native[4][2], entries)
    mass = author_mass_wire()
    empty = pack("<i", 0)
    guard_runtime()
    cases = [
        refuse("negative_count", pack("<i", -1), seed, part, "mass", "outside zero through two"),
        refuse("oversized_count", pack("<i", 3), seed, part, "mass", "outside zero through two"),
        refuse("negative_atom_count", pack("<ii", 1, -1), seed, part, "mass", "implausible SOLIDWORKS body repeat"),
        refuse("truncated_selector", mass[:-1], seed, part, "mass", "truncated SOLIDWORKS archive field"),
        refuse("mass_surplus", mass + b"\0", seed, part, "mass", "trailing data"),
        refuse("bounds_owner", pack("<iiH", 1, 13, 0), seed, part, "bounds", "requires typed owners"),
        refuse("bounds_surplus", empty + b"\0", seed, part, "bounds", "trailing data"),
        refuse("missing_part", empty, MapSnapshot(seed.CounterValue, (entries[0],)), part, "bounds", "mapped ordinary part"),
        refuse("version", empty, seed, part, "bounds", "requires archive version 19000", 18900),
    ]
    return {"case": "authored", "runtime_external_accesses": 0, "records": {
        "mass": inspect(mass, 19000, seed, part, "mass"),
        "bounds": inspect(empty, 19000, seed, part, "bounds"),
    }, "refusals": cases}


def main():
    parser = ArgumentParser(description="Verify bounded version-19000 part cache fields")
    parser.add_argument("case", choices=(*NATIVE_CASES, *DISCLOSED_CASES, "authored"))
    parser.add_argument("--disclosed-root", type=Path)
    args = parser.parse_args()
    if args.case in DISCLOSED_CASES and args.disclosed_root is None:
        parser.error("the selected native control requires its disclosed root")
    result = authored() if args.case == "authored" else read_case(
        args.case, args.disclosed_root if args.case in DISCLOSED_CASES else ROOT
    )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
