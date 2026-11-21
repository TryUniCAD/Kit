from argparse import ArgumentParser
from functools import partial
import json
from pathlib import Path
from struct import pack
from subprocess import check_output
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
sys.path[:0] = [str(ROOT / "src"), str(HERE.parent)]

from CheckCfgSection import (
    DIRECT, GHOST, KGhostFields, PART, digest, guard_runtime, load_case, missing_sibling, new_object,
    require, section_rule, sibling_reader, sized,
)
from MakeHeadAliasCase import DIRECTORY, SELF, header
from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadBodyMut import ReadBodyMut
from convert.adapters.solidworks.Archive.Bodies.WriteBodyMut import WriteBodyMut
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteNodeMut import WriteNodeMut
from convert.adapters.solidworks.Archive.Header.HeaderRefNodes import HeaderRefNodes
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Maps.FindObject import FindObject
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Archive.Reading.ReadGraphNode import ReadNodeMut
from convert.adapters.solidworks.Archive.Reading.ReadSectSpan import ReadSectSpan

VERSION = 19000
ASSEMBLY = RuntimeClass("moAssembly_c", 1)
FIRST = NativeField("Scalar", "first", "u32")
LAST = NativeField("Scalar", "last", "u32")
LINK = NativeField("Node", "link")
GHOST_ONLY = (section_rule(GHOST),)
GHOSTS = {"ladder": (10000, 1), "concave": (10000, 0), "signed": (25, -8)}
CASES = {"single": (41, 73, False), "directory": (201, 907, True)}
ACTIONS = ("WriteActions", "WriteSectionMut", "WriteDirectMut", "WriteGhostMut")
BASE = "e3b75f8860497fd92583e5397b7d0c4ac40528cf"


def layout(with_ghost):
    extra = GHOST_ONLY if with_ghost else ()
    return section_rule(DIRECT, FIRST), section_rule(LINK, LAST, *extra)


def aliases_from(header_bytes):
    return HeaderRefNodes(ReadHeaderGraph(header_bytes, VERSION), VERSION)


def ghost_fields(fresh, flags, rows=()):
    return {"f80": fresh, "fe0": flags, "objects": list(rows)}


def ghost_wire(fresh, flags):
    return pack("<ii", fresh, flags << 28)


def typed_writer(rules, aliases=(), *, version=VERSION, conditions=0, owner=PART, children=None):
    layouts = {owner.NameValue: rules, **(children or {})}
    context = BodyContext(
        version, {**KGhostFields, **layouts}, {}, dict.fromkeys(layouts, (1,)),
        FlagsValue={"conditions": conditions}, DirectNodes=aliases,
    )
    return BodyWriter(ArchiveMaps(1), context, WriteBodyMut)


def write_model(writer, node):
    output = writer.OutputValue
    WriteNodeMut(writer, node)
    require(writer.OutputValue is output and not writer.NestingDepth, "write did not restore the outer state")
    return bytes(output)


def read_model(raw, rules, aliases=()):
    context = BodyContext(
        VERSION, {**KGhostFields, PART.NameValue: rules}, {}, {PART.NameValue: (1,)},
        DirectNodes=aliases,
    )
    cursor = BinaryReader(raw)
    graph = GraphReader(cursor, ArchiveMaps(1), partial(ReadBodyMut, context))
    model = ReadNodeMut(graph)
    require(model is not None and model.EndOffset == cursor.GetOffset() == len(raw)
            and graph.Cursor is cursor, "readback did not fully consume the emitted graph")
    return model, graph.MapValue


def authored_case(mode):
    first, last, with_ghost = CASES[mode]
    typed_header = header(SELF, DIRECTORY if with_ghost else ())
    aliases = aliases_from(typed_header)
    model = {"first": first, "last": last, "link": aliases[-1]}
    if with_ghost:
        model["fd90"] = ghost_fields(*GHOSTS["signed"])
    writer = typed_writer(layout(with_ghost), aliases)
    raw = write_model(writer, ArchiveNode(PART, model))
    require(writer.MapValue.CounterValue == writer.MapValue.BaseValue == 3 + len(aliases)
            and tuple(FindObject(writer.MapValue, index) for index in range(3, 3 + len(aliases))) == aliases,
            "the writer did not allocate the canonical aliases across siblings")
    return {"wire": raw.hex(), "header": typed_header.hex()}


def authored_ghost(fresh, flags):
    writer = typed_writer(GHOST_ONLY)
    raw = write_model(writer, ArchiveNode(PART, {"fd90": ghost_fields(fresh, flags)}))
    require(writer.MapValue.BaseValue == 1 and writer.MapValue.CounterValue == 3,
            "ghost emission changed the object map")
    return raw.hex()


def refusal(label, rules, fields, message, *, aliases=(), version=VERSION, conditions=0, owner=PART, children=None):
    writer = typed_writer(rules, aliases, version=version, conditions=conditions, owner=owner, children=children)
    outer = writer.OutputValue
    try:
        WriteNodeMut(writer, ArchiveNode(owner, fields))
    except ValueError as error:
        require(message in str(error), f"{label} refused the wrong boundary")
        require(writer.OutputValue is outer and bytes(outer) == new_object(owner, b"")
                and writer.NestingDepth == 0, f"{label} published incomplete section bytes")
        return {"case": label, "diagnostic": str(error), "outer_bytes": len(outer)}
    raise ValueError(f"unqualified request was accepted: {label}")


def author_refusals():
    ref = aliases_from(header(SELF, ()))[0]
    fields = {"first": 1, "last": 2, "link": ref}
    siblings = layout(False)
    return [
        refusal("wrong_version", siblings, fields, "requires archive version 19000", version=18900, aliases=(ref,)),
        refusal("skip_lightweight", siblings, fields, "skipped model section", conditions=0x80000, aliases=(ref,)),
        refusal("skip_resolved", siblings, fields, "skipped model section", conditions=0x100000, aliases=(ref,)),
        refusal("absent_alias", siblings, fields, "needs distinct new aliases"),
        refusal("duplicate_alias", siblings, fields, "needs distinct new aliases", aliases=(ref, ref)),
        refusal("wrong_alias_class", siblings, fields, "needs distinct new aliases",
                aliases=(ArchiveNode(RuntimeClass("moNodeName_c", 1), {}),)),
        refusal("wrong_owner", siblings, fields, "unsupported SOLIDWORKS direct part header owner",
                aliases=(ref,), owner=ASSEMBLY),
        refusal("nested_part", (section_rule(NativeField("Node", "descendant")),),
                {"descendant": ArchiveNode(PART, fields)}, "unsupported SOLIDWORKS direct part header owner",
                aliases=(ref,), owner=ASSEMBLY, children={PART.NameValue: siblings}),
        *[
            refusal(label, GHOST_ONLY, {"fd90": ghost_fields(25, flags, rows)}, reason)
            for label, flags, rows, reason in (
                ("flag_underflow", -9, (), "signed four bit integer"),
                ("flag_overflow", 8, (), "signed four bit integer"),
                ("boolean_flag", True, (), "signed four bit integer"),
                ("populated_ghost", 1, ({},), "unqualified populated SOLIDWORKS ghost rows"),
            )
        ],
    ]


def author():
    guard_runtime()
    return {
        "models": {mode: authored_case(mode) for mode in CASES},
        "ghosts": {mode: authored_ghost(*spec) for mode, spec in GHOSTS.items()},
        "refusals": author_refusals(),
    }


def inspect_case(mode, issued):
    first, last, with_ghost = CASES[mode]
    raw = bytes.fromhex(issued["wire"])
    aliases = aliases_from(bytes.fromhex(issued["header"]))
    original_slots = [alias.IndexValue for alias in aliases]
    expected_slot = 2 + len(aliases)
    tail = sized(ghost_wire(*GHOSTS["signed"])) if with_ghost else b""
    independent = new_object(PART, sized(pack("<I", first)) + sized(pack("<HI", expected_slot, last) + tail))
    require(raw == independent, "independent section lengths and reference bytes disagree")
    model, maps = read_model(raw, layout(with_ghost), aliases)
    require(model.FieldsValue["link"] is aliases[-1] is FindObject(maps, expected_slot)
            and maps.CounterValue == maps.BaseValue == 3 + len(aliases)
            and tuple(FindObject(maps, index) for index in range(3, 3 + len(aliases))) == aliases,
            "readback did not use the actual direct header identities")
    require(model.FieldsValue["first"] == first and model.FieldsValue["last"] == last
            and [alias.IndexValue for alias in aliases] == original_slots,
            "sibling payload changed its values or standalone header slots")
    windows = []
    refused_alias = None
    cursor = BinaryReader(raw, 14)
    for _ in range(2):
        section = ReadSectSpan(cursor)
        windows.append([section.GetOffset(), section.GetEnd()])
        cursor.OffsetValue = section.GetEnd()
    if with_ghost:
        require(model.FieldsValue["fd90"] == {**ghost_fields(*GHOSTS["signed"]), "n": 0},
                "nested authored section lost its signed ghost fields")
    else:
        precise, observed = sibling_reader(raw, VERSION, aliases)
        require(ReadNodeMut(precise) is not None and [row["body"] for row in observed] == windows
                and [row["map_before"] for row in observed] == [[1, 3], [4, 4]]
                and [row["map_after"] for row in observed] == [[4, 4], [4, 4]],
                "the shared reader did not observe the exact sibling map boundary")
        refused_alias = missing_sibling(raw, VERSION)
    return {"case": mode, "bytes": len(raw), "wire_sha256": digest(raw), "windows": windows,
            "map_base": maps.BaseValue, "map_counter": maps.CounterValue, "config_ref_slot": expected_slot,
            "standalone_slots": original_slots, "outer_cursor": cursor.GetOffset(),
            "missing_alias": refused_alias}


def inspect_ghost(mode, wire, source):
    fresh, flags = GHOSTS[mode]
    raw = bytes.fromhex(wire)
    body = ghost_wire(fresh, flags)
    require(raw == new_object(PART, sized(body)), "independent ghost formula disagrees")
    model, maps = read_model(raw, GHOST_ONLY)
    require(model.FieldsValue["fd90"] == {**ghost_fields(fresh, flags), "n": 0}
            and (maps.BaseValue, maps.CounterValue) == (1, 3), "ghost fields or map changed")
    result = {"case": mode, "f80": fresh, "signed_flags": flags, "row_count": 0,
              "wire_sha256": digest(body), "wire_bytes": len(body)}
    if source is not None:
        config, _, _, control = source
        ghost = control["ghost"]
        start, end = ghost["interval"]
        require(body == config[start:end] and digest(body) == ghost["sha256"],
                "authored ghost bytes differ from the pinned native contrast")
        result.update(native_interval=[start, end], source_sha256=control["part_sha256"],
                      config_sha256=control["config_sha256"])
    return result


def inspect(issued):
    sources = {mode: load_case(mode) for mode in GHOSTS if mode != "signed"}
    guard_runtime()
    return {
        "models": [inspect_case(mode, issued["models"][mode]) for mode in CASES],
        "ghosts": [inspect_ghost(mode, issued["ghosts"][mode], sources.get(mode)) for mode in GHOSTS],
    }


def measure():
    source_dir = "src/convert/adapters/solidworks/Archive/Bodies/Writing"
    files = [f"{source_dir}/{name}.py" for name in ACTIONS]
    files.extend((
        "re/tooling/sw2026/CheckCfgSectionWrite.py", "re/tooling/sw2026/CheckCfgSection.py",
        "re/tooling/sw2026/MakeHeadAliasCase.py", "re/solidworks/measurements/2026/ConfigSectionSource01.json",
    ))
    command = (sys.executable, "-I", "-B", str(HERE))
    authored = check_output((*command, "author"), timeout=60)
    verified = json.loads(check_output((*command, "inspect"), input=authored, timeout=60))
    refusals = json.loads(authored)["refusals"]
    return {**verified, "refusals": refusals, "guarded_fresh_processes": 2, "runtime_external_accesses": 0,
            "tested_base": BASE, "complete_config_admission": False, "native_launches": 0,
            "source_sha256": {name: digest((ROOT / name).read_bytes()) for name in files}}


def main():
    parser = ArgumentParser()
    parser.add_argument("case", choices=("measure", "author", "inspect"))
    requested = parser.parse_args().case
    result = author() if requested == "author" else inspect(json.load(sys.stdin)) if requested == "inspect" else measure()
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
