from argparse import ArgumentParser
from codecs import lookup
from hashlib import sha256
from pathlib import Path
from struct import pack, unpack_from
import json
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
sys.path[:0] = [str(ROOT / "src"), str(HERE.parent)]

from CheckCfgOwners import audit_run
from convert.adapters.solidworks.Archive.Config.Link.ReadPartStart import ReadPartStart
from convert.adapters.solidworks.Archive.Config.SheetMetal.ReadCfgMaster import ReadCfgMaster
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Container.Container import SldprtArchive

CONTROLS = {
    "rectangle": ("RectangleProperties", "4377bf5680f30d1c9de52227928911e55604a75d30ceb987240df00d6b1b1805",
        "a77890c040efaa9792d0b151c5d38c8b9458301781c399a4a52b9b4a9d003d3a",
        "c3fd32646c92282433f0d265e0ee767256f869489c88efc0bdf41b925b9c058b",
        (25099, 25103), "df3f619804a92fdb4057192dc43dd748ea778adc52bc498ce80524c014b81119", 105, 0, None),
    "circular": ("CircularProperties", "1c1bc718661b88a119bc3ac041f97d56cf5b4a06e290e1ac1afc79d423e42d23",
        "5c78942508f55177db00ea7f394856a6d8c72683b19163b4e3d14e557fe045c7",
        "dbff4fc3e0c22cc292d30541648df2aef7e7e193c513d005ceb3cbc88e962a9a",
        (25320, 25473), "94932387d25e3870b30d38890e59a43b99967f805bed225c02ed02e929134a42", 119, 1, 1),
    "circle-save": ("CircleRadiusBoss-open-save", "2be24e233fb210e575c411ed7665d715036844859a86833bd025317c05edfee0",
        "0108db9a716df98148a4d55f6a50cbf5ae184847132ab7d065e5329676194952",
        "f69b4105ad3ebea020b533ed18a76bb8230a25cc19a03e5aab3539e4fef63fbe",
        (24214, 24367), "7bc2acf38197cb8a08008c527073ee0e12bb3186f7c4b8b597ecb94d85e4ef79", 118, 1, 0),
}


def digest(data):
    return sha256(data).hexdigest()


def require(ok, diagnostic):
    if not ok:
        raise ValueError(diagnostic)


def wide(name):
    raw = name.encode("utf-16-le")
    return b"\xff\xfe\xff" + bytes((len(raw) // 2,)) + raw


def authored_master(selector, name, *, count=0, owner=0, list_wire=b"\0\0", tail=0):
    raw = pack("<iHiIii", selector, owner, 2, 0x40000100, -1, -19) + wide(name)
    raw += pack("<iH", 0, 0) + list_wire + pack("<i", tail)
    raw += pack("<iiIB", 7, -41, 17, 1) + wide("frame λ")
    raw += pack("<iiiidiH", -4, 11, -9, 19000, -0.125, -83, 0)
    raw += wide("visible") + pack("<BHHBIHhf", 1, 0x1111, 3, 7, 0x01234567, 43, -2, 0.25)
    raw += pack("<iiHIBBiiiiiHiii", 4, -16, 0, 0xFFFF0001, 3, 2, -99, 1, 78, -349, -125,
                15, 229, -6, count)
    return raw


def report_node(node):
    require(node.ClassValue.NameValue == "moSheetMetalMaster_c" and node.ClassValue.SchemaValue == 1
            and node.IndexValue is None, "direct owner acquired a map slot")
    fields = node.FieldsValue
    require(fields["f358"] == [] and fields["n370"] == 0, "direct owner lost its empty list")
    return {"class": node.ClassValue.NameValue, "schema": node.ClassValue.SchemaValue,
            "index": node.IndexValue, "native_id": fields["f08"],
            "variant": fields["f28c"], "count": fields["n370"],
            "inherited_count_width": fields["f60"]["list"].get("n#width", 2),
            "fields_sha256": digest(json.dumps(fields, sort_keys=True, separators=(",", ":")).encode())}


def refuse(name, data, mapping, owner, diagnostic, *, version=19000):
    try:
        ReadCfgMaster(data, version, mapping, owner)
    except ValueError as error:
        require(diagnostic in str(error), f"{name} failed at another boundary: {error}")
        return name
    raise AssertionError(f"{name} was admitted")


def authored(mapping, part):
    result = []
    for selector, name in ((-7, "signed λ"), (41, "longer owner Δ")):
        raw = authored_master(selector, name)
        node = ReadCfgMaster(raw, 19000, mapping, part)
        require(node is not None and node.FieldsValue["f20"] == name and node.FieldsValue["f1e8"] == "frame λ"
                and node.FieldsValue["f28c"] == -41 and node.FieldsValue["f2a0"] == -125,
                "authored master fields did not keep their typed values")
        require(node.FieldsValue["f2c8"]["f08"]["f08"] == {"f06": -2, "f00": 0.25},
                "authored master lost the embedded visual width")
        result.append({"selector": selector, "bytes": len(raw), "sha256": digest(raw),
                       "node": report_node(node)})
    require(result[0]["bytes"] != result[1]["bytes"], "distinct names did not grow archive length")
    extended = authored_master(-7, "signed λ", list_wire=pack("<HI", 0xffff, 0))
    node = ReadCfgMaster(extended, 19000, mapping, part)
    require(node is not None and node.FieldsValue["f60"] == {
        "list": {"n": 0, "n#width": 6, "items": []}, "tail": 0,
    }, "extended empty inherited count did not retain its native width")
    compact = ReadCfgMaster(authored_master(-7, "signed λ"), 19000, mapping, part)
    require(compact is not None and {**compact.FieldsValue, "f60": node.FieldsValue["f60"]} == node.FieldsValue
            and len(extended) == result[0]["bytes"] + 4, "extended count shifted a following field")
    result.append({"selector": -7, "bytes": len(extended), "sha256": digest(extended), "node": report_node(node)})
    raw = authored_master(1, "fails")
    class_name = b"moSheetMetalMaster_c"
    tagged = raw[:4] + pack("<3H", 0xFFFF, 1, len(class_name)) + class_name + raw[4:]
    faults = [
        refuse("wrong_version", b"", mapping, part, "requires archive version 19000", version=18000),
        refuse("detached_part", raw, mapping, ArchiveNode(part.ClassValue, {}), "mapped part owner"),
        refuse("trailing_absent", pack("<ib", 0, 7), mapping, part, "master boundary"),
        refuse("missing_direct_owner", pack("<i", 1), mapping, part, "archive tag has no complete unsigned short"),
        refuse("wrong_tagged_frame", tagged, mapping, part, "master tagged body 'moSheetMetalMaster_c'"),
        refuse("borrowed_part_link", authored_master(1, "fails", owner=2), mapping, part, "master links"),
        refuse("nonempty_list", authored_master(1, "fails", count=1), mapping, part, "nonempty sheet metal master body list"),
        refuse("negative_list", authored_master(1, "fails", count=-1), mapping, part, "nonempty sheet metal master body list"),
        refuse("nonempty_inherited_list", authored_master(1, "fails", list_wire=pack("<HIH", 0xffff, 1, 0)),
               mapping, part, "master links"),
        refuse("nonzero_inherited_tail", authored_master(1, "fails", list_wire=pack("<HI", 0xffff, 0), tail=-11),
               mapping, part, "master links"),
        refuse("appended_present", raw + b"\0", mapping, part, "master boundary"),
    ]
    return {"positive": result, "refusals": faults}


def source_path(case):
    return ROOT / "re/solidworks/v2026/corpus/direct-master" / (CONTROLS[case][0] + ".SLDPRT")


def load_case(case):
    source = source_path(case)
    require(not source.is_symlink(), "native source must be the disclosed file")
    raw = source.read_bytes()
    require(digest(raw) == CONTROLS[case][1], "native source hash changed")
    return raw


def read_case(case, raw):
    _, _, config_hash, header_hash, interval, field_hash, _, selector, _ = CONTROLS[case]
    archive = SldprtArchive.from_bytes(raw)
    config = archive.require("Contents/Config-0")
    require(archive.format_version == 4 and digest(config) == config_hash
            and digest(archive.require("Contents/Config-0-ModelHeader")) == header_hash,
            "native archive framing or streams changed")
    data = config[slice(*interval)]
    require(digest(data) == field_hash and unpack_from("<i", data)[0] == selector,
            "selected model bridge interval changed")
    return archive, config, data


def run(case):
    _, source_hash, config_hash, header_hash, interval, field_hash, _, selector, variant = CONTROLS[case]
    raw = load_case(case)
    for encoding in ("ascii", "utf-16-le", "latin-1", "cp1252"):
        lookup(encoding)
    sys.addaudithook(audit_run)
    archive, _, data = read_case(case, raw)
    prefix = ReadPartStart(archive)
    require(prefix.RootValue.IndexValue == 2 and prefix.BaseValue == 4, "wrong native part prefix")
    seed = prefix.MapValue
    node = ReadCfgMaster(data, 19000, seed, prefix.RootValue)
    if selector == 0:
        require(node is None and len(data) == 4, "zero selector consumed a direct feature")
    else:
        require(node is not None and len(data) == 153 and node.FieldsValue["f08"] == -1
                and node.FieldsValue["f28c"] == variant, "direct feature differs from the native record")
    result = {"case": case, "interval": interval, "base": prefix.BaseValue,
              "prefix_counter": seed.CounterValue, "prefix_slots": [entry.IndexValue for entry in seed.EntriesValue],
              "selector": selector, "body_bytes": len(data) - 4,
              "source_sha256": source_hash, "config_sha256": config_hash,
              "header_sha256": header_hash, "bridge_sha256": field_hash,
              "result": None if node is None else report_node(node), "runtime_external_accesses": 0}
    if case == "circular":
        result["authored"] = authored(seed, prefix.RootValue)
    require(not prefix.RootValue.FieldsValue, "reader mutated the inherited part owner")
    return result


if __name__ == "__main__":
    parser = ArgumentParser(description="Verify the bounded sheet-metal master bridge")
    parser.add_argument("case", choices=tuple(CONTROLS))
    print(json.dumps(run(parser.parse_args().case), sort_keys=True))
