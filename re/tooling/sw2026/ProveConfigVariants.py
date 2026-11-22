from argparse import ArgumentParser
from codecs import lookup
import json
from pathlib import Path
from struct import pack
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from CheckOrdinaryCfg import (
    LANE, check_owners, guard_runtime, identity, open_case, read_scope, rejection, require,
)
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadLengthMut import ReadLengthMut
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadOwnedMut import ReadOwnedMut
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadPresentMut import ReadPresentMut
from convert.adapters.solidworks.Archive.Config.ReadConfigMut import ReadConfigMut
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Container.Container import SldprtArchive

MASTER = RuntimeClass("moSheetMetalMaster_c", 1)
DENSITY = RuntimeClass("moDensityUnits_c", 1)
LENGTH = RuntimeClass("moLengthUserUnits_c", 1)
SIGNED = {"nec8": -7, "nff4": -13, "n10c4": -19, "m": -29}
ROWS = {"nec8": "fec0", "nff4": "ffe0", "n10c4": "f10b0"}
PRESENT_NULL = 167
PRESENT_LENGTH = 99


def authored_master():
    fields = dict.fromkeys((
        "f0c", "f28", "f2c", "has_list68", "f298", "f28c", "f29c", "has_f1e8",
        "f2a8", "f2b8", "f2bc", "f2b0", "f2b4", "f1f4", "f2ec", "fa8", "f208",
        "f300", "f301", "f318", "f30c", "f2a4", "f2a0", "f98", "f2ac", "f344", "n370",
    ), 0)
    fields.update(dict.fromkeys(("f18", "f78", "f258", "f2f0")))
    fields.update({
        "f08": -1,
        "f20": ("A", "Queue-authored inline master"),
        "f60": {"list": {"items": []}, "tail": 0},
        "f1e0": 0.0,
        "f1f8": ("A", ""),
        "f2c8": {"f00": 0, "f02": 0, "f04": 0,
                 "f08": {"f00": 5, "f04": 0, "f08": {"f06": 0, "f00": 0.5}}},
        "hidden": 1,
        "f358": [],
    })
    return ArchiveNode(MASTER, fields)


def nodes(graph, concrete):
    return [
        entry.EntryValue for entry in graph.MapValue.EntriesValue
        if isinstance(entry.EntryValue, ArchiveNode)
        and entry.EntryValue.ClassValue == concrete
    ]


def author_fields(graph):
    root = graph.RootValue.FieldsValue
    require(not root["f1014"] and "f1018" not in root, "native base already contains the inline master")
    first, second = nodes(graph, DENSITY)
    length_fields = dict(nodes(graph, LENGTH)[-1].FieldsValue)
    length_fields.update({"f88": 0.0, "fb8": None})
    length = ArchiveNode(LENGTH, length_fields)
    first.FieldsValue.update({"has_fb8": PRESENT_NULL, "fb8": None})
    second.FieldsValue.update({"has_fb8": PRESENT_LENGTH, "fb8": length})
    for field, rows in ROWS.items():
        root[field] = SIGNED[field]
        root[rows] = []
    root.update({
        "n1290": -23,
        "f1288": [{"v": 0x12345678}, {"v": 0xABCDEF01}],
        "f1d0": [{"k0": ("A", "Queue auth"), "k1": ("A", "Nested empty"),
                  "m": SIGNED["m"], "pairs": []}],
        "f1014": 1,
        "f1018": authored_master(),
    })
    return first


def read_witnesses(wire, header):
    differences = {"flags": [], "lengths": {}, "master": []}

    def profile(frame, event, _argument):
        code = frame.f_code
        if (code is not ReadPresentMut.__code__
                and code is not ReadLengthMut.__code__
                and code is not ReadOwnedMut.__code__):
            return
        state = frame.f_locals["FrameValue"]
        rule = frame.f_locals["RuleValue"]
        cursor = state.ReaderValue.Cursor
        if (event == "call" and code is ReadPresentMut.__code__
                and state.NodeValue.ClassValue == DENSITY and rule.NameValue == "has_fb8"):
            differences["flags"].append(cursor.OffsetValue)
        if (event == "call" and code is ReadLengthMut.__code__
                and state.NodeValue is state.ContextValue.PartRootValue
                and rule.NameValue in (*SIGNED, "n1290")):
            differences["lengths"][rule.NameValue] = cursor.OffsetValue
        if code is ReadOwnedMut.__code__ and rule.NameValue == "f1018":
            differences["master"].append((event, cursor.OffsetValue, state.ReaderValue.MapValue.CounterValue))

    prior = sys.getprofile()
    sys.setprofile(profile)
    try:
        graph = ReadConfigMut(wire, 19000, header)
    finally:
        sys.setprofile(prior)
    return graph, differences


def check_fields(wire, graph, evidence):
    first, second = nodes(graph, DENSITY)
    begin, peer = evidence["flags"]
    length = second.FieldsValue["fb8"]
    require(first.FieldsValue["has_fb8"] == PRESENT_NULL and first.FieldsValue["fb8"] is None
            and wire[begin:begin + 3] == pack("<BH", PRESENT_NULL, 0),
            "density presence or its explicit null was lost")
    require(second.FieldsValue["has_fb8"] == wire[peer] == PRESENT_LENGTH
            and length.ClassValue == LENGTH and length.FieldsValue["f88"] == 0.0
            and length is nodes(graph, LENGTH)[-1],
            "density presence or resolved length-format owner changed")
    root = graph.RootValue.FieldsValue
    for field, values in ROWS.items():
        require(root[field] == SIGNED[field] and root[values] == [],
                "signed empty repeat changed its retained length or rows")
    nested, = root["f1d0"]
    require(nested["m"] == SIGNED["m"] and nested["pairs"] == [],
            "nested signed repeat changed its wire length or rows")
    require(root["n1290"] == 2 and root["f1288"] == [{"v": 0x12345678}, {"v": 0xABCDEF01}],
            "changed modeled rows failed to derive their count")
    for field, value in {**SIGNED, "n1290": 2}.items():
        offset = evidence["lengths"][field]
        require(wire[offset:offset + 4] == pack("<i", value), "signed wire length differs")
    owner = root["f1018"]
    (entry, start, before), (exit_event, end, after) = evidence["master"]
    require((entry, exit_event) == ("call", "return") and start < end and before == after
            and root["f1014"] == 1 and owner.ClassValue == MASTER and owner.IndexValue is None
            and owner.FieldsValue["f20"] == ("A", "Queue-authored inline master")
            and owner.FieldsValue["f358"] == []
            and owner.FieldsValue["f2c8"]["f08"]["f08"]["f00"] == 0.5
            and all(row.EntryValue is not owner for row in graph.MapValue.EntriesValue),
            "the inline master lost class, fields or by-value ownership")
    return [start, end, before, after]


def check_refusals(graph, density):
    root = graph.RootValue.FieldsValue
    owner = root["f1018"]
    emit = lambda: WriteConfigMut(graph.RootValue, 19000, graph.HeaderValue)
    root["f1018"] = ArchiveNode(LENGTH, {})
    wrong = rejection(emit, "native directly owned object has the wrong class")
    root["f1018"] = owner
    owner.FieldsValue["f358"] = [{}]
    populated = rejection(emit, "nonempty sheet metal master body list")
    owner.FieldsValue["f358"] = []
    del density.FieldsValue["fb8"]
    missing = rejection(emit, "native object presence requires its modeled field")
    return {"wrong_master": wrong, "populated_master": populated, "missing_density_field": missing}


def measure():
    raw, pin = open_case("concave")
    for encoding in ("ascii", "latin-1", "utf-8", "utf-16-le"):
        lookup(encoding)
    with guard_runtime() as accesses:
        archive = SldprtArchive.from_bytes(raw)
        original, _ = read_scope(archive)
        baseline, original_write = WriteConfigMut(original.RootValue, 19000, original.HeaderValue)
        require(baseline == archive.require(LANE), "source configuration changed before the contrast")
        check_owners(original, original_write)
        density = author_fields(original)
        wire, emitted = WriteConfigMut(original.RootValue, 19000, original.HeaderValue)
        graph, evidence = read_witnesses(wire, original.HeaderValue)
        master = check_fields(wire, graph, evidence)
        replay, replay_graph = WriteConfigMut(graph.RootValue, 19000, graph.HeaderValue)
        check_owners(graph, replay_graph)
        require(replay == wire and graph.MapValue.CounterValue == emitted.MapValue.CounterValue,
                "authored control changed on typed replay")
        refusals = check_refusals(original, density)
    require(not accesses and open_case("concave") == (raw, pin), "guarded proof altered its source")
    return {
        "case": "authored", "source_sha256": pin, "native_source_bytes": len(baseline),
        "runtime_external_accesses": len(accesses), "complete_replay": True,
        "model_config_sha256": identity(wire), "model_config_bytes": len(wire),
        "map_base": graph.MapBase, "final_map_counter": graph.MapValue.CounterValue,
        "density_presence": [PRESENT_NULL, PRESENT_LENGTH], "density_present_null": True,
        "wire_lengths": {**SIGNED, "n1290": 2}, "direct_master": master,
        "refusals": refusals,
    }


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("case", choices=("authored",))
    parser.parse_args()
    print(json.dumps(measure(), sort_keys=True, allow_nan=False))
