from argparse import ArgumentParser
from codecs import lookup
import json
from pathlib import Path
from struct import pack
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
sys.path[:0] = [str(ROOT / "src"), str(HERE.parent)]

from CheckCfgMembers import digest, require
from CheckCfgOwners import audit_run
from convert.adapters.solidworks.Archive.Config.Link.CheckPartRoot import KPartRoot
from convert.adapters.solidworks.Archive.Config.Link.ReadPartStart import ReadPartStart
from convert.adapters.solidworks.Archive.Config.Material.ReadPartMat import ReadPartMat
from convert.adapters.solidworks.Archive.Maps.MapSnapshot import MapSnapshot
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Container.Container import SldprtArchive

MANIFEST = ROOT / "re/solidworks/measurements/2026/ConfigMaterialSource01.json"


def load_case(name):
    manifest = json.loads(MANIFEST.read_bytes())
    case = manifest["controls"][name]
    content = (ROOT / case["path"]).read_bytes()
    require(digest(content) == case["part_sha256"], "native material source changed")
    archive = SldprtArchive.from_bytes(content)
    for key in ("config", "header"):
        data = archive.require(manifest[key + "_stream"])
        assert len(data) == case[key + "_bytes"] and digest(data) == case[key + "_sha256"]
    return archive, archive.require(manifest["config_stream"]), manifest["archive_version"], case


def shape(value):
    if isinstance(value, ArchiveNode):
        return {"class": [value.ClassValue.NameValue, value.ClassValue.SchemaValue],
                "slot": value.IndexValue, "fields": shape(dict(value.FieldsValue))}
    if isinstance(value, dict):
        return {key: shape(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [shape(item) for item in value]
    return value


def seed_material(archive, case):
    start = ReadPartStart(archive)
    assert case["light_interval"] == [start.LightOffset, start.LightOffset + start.LightSize]
    lower, upper = case["group_interval"]
    assert start.LightOffset <= lower < upper <= start.LightOffset + start.LightSize
    entries = start.MapValue.EntriesValue
    assert [entry.IndexValue for entry in entries] == [1, 2, 3] and start.BaseValue == 4
    assert entries[1].EntryValue is start.RootValue
    assert entries[2].EntryValue is start.HeaderValue.FieldsValue["f38"]
    assert entries[2].EntryValue.IndexValue == case["header_standalone_slot"]
    return start.RootValue, MapSnapshot(case["counter"][0], entries)


def entry_shape(entry):
    value = entry.EntryValue
    cls = value.ClassValue if isinstance(value, ArchiveNode) else value
    return [entry.IndexValue, "object" if isinstance(value, ArchiveNode) else "class",
            cls.NameValue, cls.SchemaValue]


def check_owner(config, group_start, observation, decoded):
    begin, end = observation["interval"]
    assert digest(config[begin:end]) == observation["wire_sha256"]
    value = decoded.FieldsValue[observation["field"]]
    representation = shape(value)
    assert digest(json.dumps(representation, sort_keys=True, separators=(",", ":")).encode()) == observation["typed_sha256"]
    counter, final = observation["counter"]
    entries = [entry for entry in decoded.MapValue.EntriesValue if counter <= entry.IndexValue < final]
    assert [entry_shape(entry) for entry in entries] == observation["entries"]
    spans = observation["spans"]
    if spans:
        nodes = {"owner": value}
        if "density" in spans:
            nodes["density"] = value.FieldsValue["f08"]
        for key, node in nodes.items():
            assert (node.StartOffset, node.EndOffset) == tuple(offset - group_start for offset in spans[key])
            assert next(entry for entry in entries if entry.IndexValue == node.IndexValue).EntryValue is node
            assert any(entry.EntryValue is node.ClassValue for entry in entries)


def native_summary(fields):
    hatch = fields["f1418"]
    material = fields["f1420"]
    model = fields["f1588"]
    density = None if material is None else material.FieldsValue["f08"]
    assert model.FieldsValue["f08"] is None
    if density is not None:
        assert density.FieldsValue["f18"] is None and density.FieldsValue["f48"] is None
        assert density.FieldsValue["f68"] == 0 and "f60" not in density.FieldsValue
    return {"hatch": hatch.IndexValue, "material": None if material is None else material.IndexValue,
            "density": None if density is None else density.IndexValue,
            "density_value": None if density is None else density.FieldsValue["f58"],
            "model_data": model.IndexValue, "model_word": model.FieldsValue["f10"]}


def native_read(config, version, case, model, seed):
    start, end = case["group_interval"]
    data = config[start:end]
    assert digest(data) == case["group_sha256"]
    decoded = ReadPartMat(data, version, seed, model)
    assert decoded.ReportValue["completed"] and not model.FieldsValue
    before = seed.EntriesValue
    assert all(old is new for old, new in zip(before, decoded.MapValue.EntriesValue[:len(before)], strict=True))
    assert [seed.CounterValue, decoded.MapValue.CounterValue] == case["counter"]
    for row in case["owners"]:
        check_owner(config, start, row, decoded)
    summary = native_summary(decoded.FieldsValue)
    assert summary == case["typed"]
    assert decoded.FieldsValue["f938"] == {"n08": 0, "bodies": [], "n58": 0, "props": []}
    return summary, decoded


def ref(slot):
    return pack("<H", slot)


def clsref(slot):
    return ref(0x8000 | slot)


def new_class(name):
    encoded = name.encode("ascii")
    return pack("<HHH", 0xFFFF, 1, len(encoded)) + encoded


def author_records(slots, *, density_flag=0, scene=None, parameter_name=0, viz=(0, 0)):
    hatch = clsref(slots["gcXhatch_c"]) + b"\x09Kit hatch"
    hatch += pack("<dd6i", -0.375, 1.5, -7, 21, -3, 5, -9, 6)
    density = clsref(slots["moDensityParameter_c"])
    density += pack("<HiIii", parameter_name, -31, 0x40000004, -27, 3)
    density += b"\x03rho" + pack("<HdB", 0, 1234.5, density_flag)
    if density_flag:
        density += pack("<d", 4321.5)
    material = clsref(slots["moMaterial_c"]) + density
    model = clsref(slots["uoModelData_c"]) + (ref(0) if scene is None else scene) + pack("<i", -11)
    return hatch, material, model, pack("<ii", *viz)


def authored_read(model, seed, slots):
    data = b"".join(author_records(slots))
    decoded = ReadPartMat(data, 19000, seed, model)
    fields = decoded.FieldsValue
    nodes = (fields["f1418"], fields["f1420"], fields["f1420"].FieldsValue["f08"], fields["f1588"])
    entries = decoded.MapValue.EntriesValue
    assert decoded.ReportValue["completed"]
    assert all(old is new for old, new in zip(seed.EntriesValue, entries[:-4], strict=True))
    for node, entry in zip(nodes, entries[-4:], strict=True):
        assert entry.EntryValue is node
        assert node.ClassValue is next(
            inherited.EntryValue for inherited in seed.EntriesValue
            if inherited.IndexValue == slots[node.ClassValue.NameValue]
        )
    hatch, _material, density, data_node = nodes
    assert hatch.FieldsValue["f08"] == ("A", "Kit hatch")
    assert density.FieldsValue["f20"] == ("A", "rho")
    assert density.FieldsValue["f68"] == 0 and "f60" not in density.FieldsValue
    assert data_node.FieldsValue["f08"] is None
    return {"bytes": len(data), "counter": [seed.CounterValue, decoded.MapValue.CounterValue],
            "slots": [node.IndexValue for node in nodes],
            "spans": [[node.StartOffset, node.EndOffset] for node in nodes],
            "hatch": [
                hatch.FieldsValue[key]
                for key in ("f08", "f10", "f18", "f34", "f20", "f24", "f28", "f2c", "f30")
            ],
            "density": [density.FieldsValue[key] for key in ("f0c", "f08", "f58", "f68")],
            "model_word": data_node.FieldsValue["f10"]}


def refuse(label, data, seed, model, expected, *, version=19000, flags=0):
    try:
        ReadPartMat(data, version, seed, model, ConditionBits=flags)
    except ValueError as error:
        require(expected in str(error), f"{label} gave a different reason: {error}")
        return label
    raise AssertionError(f"{label} admitted an unqualified material suffix")


def authored_bad(model, seed, slots, originals):
    hatch, mat, data, viz = author_records(slots)
    body = hatch + mat + data + viz
    mtag = clsref(slots["moMaterial_c"])
    return [
        refuse("truncated", body[:-1], seed, model, "truncated SOLIDWORKS archive field"),
        refuse("trailing", body + b"\x00", seed, model, "trailing data"),
        refuse("wrong_version", body, seed, model, "archive version 19000", version=18999),
        refuse("wrong_conditions", b"", seed, model, "material archive conditions", flags=0x80),
        refuse("detached_part", body, seed, ArchiveNode(KPartRoot, {}), "requires its mapped part owner"),
        refuse("null_hatch", ref(0) + mat + data + viz, seed, model, "requires gcXhatch_c"),
        refuse("borrowed_hatch", ref(originals["hatch"]) + mat + data + viz, seed, model, "newly read owners"),
        refuse("wrong_role", data + mat + hatch + viz, seed, model, "unsupported SOLIDWORKS lightweight material body owner"),
        refuse("null_density", hatch + mtag + ref(0) + data + viz, seed, model, "requires moDensityParameter_c"),
        refuse("borrowed_density", hatch + mtag + ref(originals["density"]) + data + viz,
               seed, model, "newly read owners"),
        refuse("wrong_density_class", hatch + mtag + data + data + viz,
               seed, model, "unsupported SOLIDWORKS lightweight material body owner"),
        refuse("density_override", b"".join(author_records(slots, density_flag=1)),
               seed, model, "unsupported SOLIDWORKS native field path alternate part density"),
        refuse("density_name_alias", b"".join(author_records(slots, parameter_name=3)),
               seed, model, "unqualified SOLIDWORKS part density links"),
        refuse("null_model_data", hatch + mat + ref(0) + viz, seed, model, "requires uoModelData_c"),
        refuse("scene_alias", b"".join(author_records(slots, scene=ref(3))),
               seed, model, "unqualified SOLIDWORKS model data scene"),
        refuse("scene_body", b"".join(author_records(slots, scene=new_class("uoScene"))),
               seed, model, "unsupported SOLIDWORKS lightweight material body owner"),
        refuse("body_visual_rows", b"".join(author_records(slots, viz=(1, 0))),
               seed, model, "populated SOLIDWORKS body visual records"),
        refuse("body_visual_properties", b"".join(author_records(slots, viz=(0, 1))),
               seed, model, "populated SOLIDWORKS body visual properties"),
    ]


def run(name):
    archive, config, version, case = load_case(name)
    for codec in ("ascii", "latin-1", "utf-16-le", "cp1252"):
        lookup(codec)
    sys.addaudithook(audit_run)
    model, seed = seed_material(archive, case)
    native, decoded = native_read(config, version, case, model, seed)
    output = {"group_interval": case["group_interval"], "counter": case["counter"], "native": native,
              "header_standalone_slot": case["header_standalone_slot"], "runtime_external_accesses": 0,
              "inherited_slots": [entry.IndexValue for entry in seed.EntriesValue]}
    if name == "ladder":
        inherited = decoded.MapValue
        slots = {entry.EntryValue.NameValue: entry.IndexValue for entry in inherited.EntriesValue
                 if type(entry.EntryValue) is RuntimeClass}
        output.update(authored=authored_read(model, inherited, slots),
                      refusals=authored_bad(model, inherited, slots, native))
    return output


def main():
    parser = ArgumentParser(description="Verify disclosed lightweight part material and model data records")
    parser.add_argument("case", choices=("ladder", "concave"))
    print(json.dumps(run(parser.parse_args().case), sort_keys=True))


if __name__ == "__main__":
    main()
