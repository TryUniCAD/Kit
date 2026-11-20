from argparse import ArgumentParser
from codecs import lookup
from functools import partial
import json
from pathlib import Path
from struct import pack
from subprocess import check_output
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from CheckPartCmgr import (
    ROOT, SOURCES, STREAM, VERSION, audit, class_tag, digest, inspect_graph,
    read_source, reject_body, require,
)
from convert.adapters.solidworks.Archive.Bodies.BodyReport import GetBodyReport
from convert.adapters.solidworks.Archive.Bodies.BodyUsage import BodyUsage
from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.ReadBodyMut import ReadBodyMut
from convert.adapters.solidworks.Archive.Bodies.WriteBodyMut import WriteBodyMut
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteNodeMut import WriteNodeMut
from convert.adapters.solidworks.Archive.Cmgr.MakeCmgrContext import MakeCmgrContext
from convert.adapters.solidworks.Archive.Cmgr.ProjectCmgrRows import ProjectCmgrRows
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Archive.Construction.Configuration.ConfigSpec import ConfigSpec
from convert.adapters.solidworks.Archive.Construction.Configuration.MakeConfigMgr import MakeConfigMgr
from convert.adapters.solidworks.Archive.Construction.Configuration.ManagerInput import ManagerInput
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import FeatureTarget
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Archive.Reading.ReadGraphNode import ReadNodeMut
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive

CASES = (*SOURCES, "authored", "refuse")


def guard_access():
    attempts = []

    def observe(event, args):
        try:
            audit(event, args)
        except RuntimeError:
            attempts.append(event)
            raise

    for encoding in ("ascii", "utf-8", "utf-16-le", "latin-1", "cp1252"):
        lookup(encoding)
    sys.addaudithook(observe)
    return attempts


def describe(graph, data):
    trace = inspect_graph((graph.RootValue, graph.MapValue, graph.ReportValue), data)
    rows = ProjectCmgrRows(graph.RootValue)
    require(rows == ({
        "name": trace["configuration"],
        "comment": trace["comment"],
        "alternate_name": trace["alternate_name"],
        "feature_description": trace["description"],
        "native_object_id": 0,
        "native_class": "moPartConfiguration_c",
        "selected_by_f360": True,
        "selected_by_f368": True,
    },), "SDK projection differs from the witnessed directory and selectors")
    require(not any(graph.ContextValue.values()), "manager left an active context")
    require(
        trace["actions"].get("Context", 0) > 0
        and trace["actions"].get("Virtual", 0) > 0
        and "moFeature_c.SerializeXmlData" in trace["layouts"],
        "manager did not exercise context and the real configuration virtual",
    )
    return trace


def exact_reissue(data):
    graph = ReadCmgrMut(data, VERSION)
    observed = describe(graph, data)
    usages = BodyUsage()
    emitted = WriteCmgrMut(graph.RootValue, VERSION, UsageValue=usages)
    require(emitted == data, "shared manager serializer changed the stream")
    report = GetBodyReport(usages)
    keys = ("completed", "used_schemas", "schema_calls", "field_calls", "missing_schemas")
    require(all(report[key] == graph.ReportValue[key] for key in keys),
            "manager read and write reached different grammar")
    require(describe(ReadCmgrMut(emitted, VERSION), emitted) == observed,
            "shared manager serializer changed the maps, aliases or field spans")
    return observed


def disclosed(case, raw):
    _, _, stream_hash, size, counter, layouts = SOURCES[case]
    archive = SldprtArchive.from_bytes(raw)
    require(archive.format_version == 4 and ContainerMo(archive.streams) == VERSION,
            "disclosed file does not use ordinary manager framing")
    observed = exact_reissue(archive.require(STREAM))
    require((observed["sha256"], observed["bytes"], observed["map_counter"],
             len(observed["layouts"])) == (stream_hash, size, counter, layouts),
            "shared executor differs from the pinned disclosed measurement")
    require((observed["name"] is None) == (case == "l1")
            and observed["configuration"] == "Default",
            "shared executor differs from the disclosed names")
    return {"source_sha256": digest(raw), "source": observed}


def fresh_manager(name):
    spec = ConfigSpec("Face inspection Ω", "Driver λ", 1795123456)
    owner = ArchiveNode(RuntimeClass("moPart_c", 1), {})
    return MakeConfigMgr(ManagerInput(name, (spec,), 0), owner, FeatureTarget(2026323, 370108))


def authored():
    result = {}
    for name, wanted in ((None, (4, 9)), ("Panel frame π", (6, 10))):
        manager = fresh_manager(name)
        selected = manager.FieldsValue["f360"]
        selected.FieldsValue.update(f498="alternate α", f1f8="feature note 🧭")
        output = WriteCmgrMut(manager, VERSION)
        observed = exact_reissue(output)
        require((observed["name"], observed["configuration"], observed["comment"],
                 observed["alternate_name"], observed["description"], observed["updated_at"]) ==
                (name, "Face inspection Ω", "Driver λ", "alternate α", "feature note 🧭", 1795123456),
                "fresh manager changed independent authored fields")
        require((observed["config_slot"], observed["map_counter"]) == wanted,
                "manager name presence did not allocate the predicted map")
        require(manager.IndexValue is selected.IndexValue is None
                and manager.FieldsValue["f368"] is selected
                and manager.FieldsValue["f370"]["items"][0]["o"] is selected,
                "manager serialization mutated the fresh source aliases or map slots")
        result["unnamed" if name is None else "named"] = observed
    return result


def wrong_virtual(name, target):
    context = MakeCmgrContext(VERSION, None)
    context.VirtualValue = context.VirtualValue | {(name, 0x3F8): target}
    return context


def write_wrong_virtual(root, owner, target):
    writer = BodyWriter(ArchiveMaps(1), wrong_virtual(owner, target), WriteBodyMut)
    WriteNodeMut(writer, root)


def read_wrong_virtual(data, owner, target):
    context = wrong_virtual(owner, target)
    reader = GraphReader(BinaryReader(data), ArchiveMaps(1), partial(ReadBodyMut, context))
    ReadNodeMut(reader)


def refuse():
    manager = fresh_manager(None)
    data = WriteCmgrMut(manager, VERSION)
    empty_list = class_tag("suObList", 1) + pack("<H", 0)
    wrong_schema = class_tag("moConfigurationMgr_c", 2)
    diagnostics = [
        reject_body("version", lambda: ReadCmgrMut(data, 18900), "archive version 18900"),
        reject_body("wrong_root", lambda: ReadCmgrMut(empty_list, VERSION), "requires its configuration manager root"),
        reject_body("wrong_schema", lambda: ReadCmgrMut(wrong_schema, VERSION), "schema"),
        reject_body("truncated", lambda: ReadCmgrMut(data[:-1], VERSION), "truncated"),
        reject_body("trailing", lambda: ReadCmgrMut(data + b"\0", VERSION), "trailing bytes"),
    ]
    for operation, value in ((write_wrong_virtual, manager), (read_wrong_virtual, data)):
        for owner, target in (("moConfigurationMgr_c", 0),
                              ("moPartConfiguration_c", "moFeature_c.SerializeXmlData")):
            diagnostics.append(reject_body(
                f"{operation.__name__}:{owner}", partial(operation, value, owner, target),
                "virtual flag requires a boolean target",
            ))
    manager.FieldsValue["f360"].FieldsValue.update(hasb88=1, fb88={})
    diagnostics.append(reject_body(
        "populated_3d_print", lambda: WriteCmgrMut(manager, VERSION), "mo3DPrintSettings_c.load",
    ))
    return {"refusals": diagnostics}


def run_case(case):
    raw = read_source(case) if case in SOURCES else None
    attempts = guard_access()
    if raw is not None:
        result = disclosed(case, raw)
    else:
        result = authored() if case == "authored" else refuse()
    require(not attempts, "manager runtime attempted external access")
    return result | {"case": case, "runtime_external_attempts": len(attempts)}


def run_all():
    records = {}
    for case in CASES:
        command = (sys.executable, "-I", "-B", __file__, case)
        first, second = (check_output(command, cwd=ROOT) for _ in range(2))
        require(first == second, f"shared CMgr process drifted: {case}")
        records[case] = json.loads(first)
    return {"processes": 2 * len(CASES), "cases": records}


def main():
    parser = ArgumentParser(description="Verify shared ordinary part CMgr encoding")
    parser.add_argument("case", choices=(*CASES, "all"))
    case = parser.parse_args().case
    print(json.dumps(run_all() if case == "all" else run_case(case),
                     ensure_ascii=True, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
