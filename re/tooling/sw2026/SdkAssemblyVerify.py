from base64 import b64decode
from codecs import lookup
from hashlib import sha256
import json
from pathlib import Path
import sys
import os
from xml.etree.ElementTree import fromstring, tostring

ROOT = Path(sys.argv[1])
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

AUDIT = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
sys.addaudithook(AUDIT.InspectEvent)

from convert.adapters.solidworks.Archive.Bodies.BodyReport import GetBodyReport
from convert.adapters.solidworks.Archive.Bodies.BodyUsage import BodyUsage
from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.CmgrHeader.ReadMgrHdrMut import ReadMgrHdrMut
from convert.adapters.solidworks.Archive.CmgrHeader.WriteMgrHdrMut import WriteMgrHdrMut
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Definition.ReadModelDef import ReadModelDef
from convert.adapters.solidworks.Archive.Definition.WriteModelDef import WriteModelDef
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.History.ReadHistMut import ReadHistMut
from convert.adapters.solidworks.Archive.History.WriteHistMut import WriteHistMut
from convert.adapters.solidworks.Archive.Mates.ReadMatesMut import ReadMatesMut
from convert.adapters.solidworks.Archive.Mates.WriteMatesMut import WriteMatesMut
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadFileKey
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

CODECS = tuple(lookup(name) for name in ("utf-16-le", "utf-8", "latin-1"))
REQUEST = json.load(sys.stdin)
AUDIT.BeginBuild()


def require(value, message):
    if not value:
        raise ValueError(message)


def roundtrips(archive, has_mates):
    streams = {item.name: item.data for item in archive.records}
    link = ReadNativeLink(archive, 0)
    header = link.ConfigValue.HeaderValue
    config_bytes, config = WriteConfigMut(link.ConfigValue.RootValue, 19000, header)
    resolved_bytes, resolved = WriteResolMut(link.ResolvedValue.RootsValue, link.ResolvedValue.ExtraFields, 19000, config.MapValue, link.ResolvedValue.ContextValue)
    usage = BodyUsage()
    manager = ReadCmgrMut(streams["Contents/CMgr"], 19000)
    actual = {"Contents/Config-0": config_bytes, "Contents/Config-0-ResolvedFeatures": resolved_bytes,
              "Contents/CMgr": WriteCmgrMut(manager.RootValue, 19000, UsageValue=usage)}
    reports = [config.ReportValue, resolved.ReportValue, GetBodyReport(usage)]
    for name in ("Header2", "Contents/Config-0-ModelHeader"):
        actual[name] = WriteHeadGraph(ReadHeaderGraph(streams[name], 19000), 19000)
    manager_header = ReadMgrHdrMut(streams["Contents/CMgrHdr2"], 19000)
    actual["Contents/CMgrHdr2"], repeated = WriteMgrHdrMut(manager_header.RootValue, 19000)
    reports.extend((manager_header.ReportValue, repeated.ReportValue))
    definition = ReadModelDef(streams["Contents/Definition"], 19000)
    actual["Contents/Definition"] = WriteModelDef(definition.GraphValue).OutputValue
    for name in ("_MO_VERSION_19000/History", "_MO_VERSION_19000/Biography"):
        graph = ReadHistMut(streams[name], 19000)
        actual[name], repeated = WriteHistMut(graph.RootValue, 19000)
        reports.extend((graph.ReportValue, repeated.ReportValue))
    mates = None
    if has_mates:
        mates = ReadMatesMut(streams["Contents/Config-0-MatesList"], link.ResolvedValue)
        actual["Contents/Config-0-MatesList"], repeated = WriteMatesMut(mates.RootsValue, resolved)
        reports.extend((mates.ReportValue, repeated.ReportValue))
    for name in streams.keys() - actual.keys():
        require(name.startswith("swXmlContents/"), "unclassified native stream role")
        prefix = b"\x86" if name.endswith("KeyWords") else b""
        root = fromstring(streams[name][len(prefix):])
        xml = tostring(root, encoding="utf-8")
        if name.endswith("COMPINSTANCETREE"):
            xml = xml.replace(b"ns0:", b"").replace(b":ns0=", b"=")
        if has_mates:
            xml = xml.replace(b" />", b"/>")
        actual[name] = prefix + b'<?xml version="1.0" encoding="UTF-8"?>\r\n' + xml + b"\r\n"
    require(actual.keys() == streams.keys() and all(actual[name] == streams[name] for name in streams), "generated native streams changed on independent typed round trip")
    require(all(report["completed"] and not report["missing_schemas"] and not report["provisional_schemas"] for report in reports), "generated graph has incomplete native grammar")
    return link, mates, manager_header, manager, {name: {"bytes": len(data), "sha256": sha256(data).hexdigest(), "byte_identity": True} for name, data in actual.items()}


def inspect(parent, mates, mgr_header, manager, child, built, request):
    model = parent.ConfigValue.RootValue
    header = parent.ConfigValue.HeaderValue
    occurrences = tuple(row["o"] for row in model.FieldsValue["f68"]["list"]["items"])
    require(len(occurrences) == model.FieldsValue["f1560"] == header.FieldsValue["fc4"] == 2, "actual direct occurrence counts differ")
    directory, = header.FieldsValue["f30"].FieldsValue["items"]
    require(all(node.FieldsValue["f3b0"] is directory for node in occurrences) and directory.FieldsValue["f48"] == 2, "actual direct external directory alias or users differ")
    require(ReadFileKey(directory) == ReadFileKey(child.ConfigValue.HeaderValue.FieldsValue["f38"]), "directory targets a different generated child identity")
    require(directory.FieldsValue["f60"] == child.ConfigValue.HeaderValue.FieldsValue["f38"].FieldsValue["f60"], "directory child self save event differs")
    require(directory.FieldsValue["f70"] == request["child"]["settings"]["output"]["saved_at"], "directory manager save event differs")
    for reference in occurrences:
        external = reference.FieldsValue["f4f8"]
        require(external.FieldsValue["f50"] is reference and external.FieldsValue["f44"] == reference.FieldsValue["f08"], "occurrence lost its actual external feature backlink")
    configuration = manager.RootValue.FieldsValue["f360"]
    require(configuration is manager.RootValue.FieldsValue["f368"] and configuration.FieldsValue["f85c"] == built["next_id"] - 1, "actual active configuration or allocation watermark differs")
    states = configuration.FieldsValue["fce8"]
    require(len(states) == 3 and states[0]["o"].FieldsValue["f10"] is None, "configuration lost its independent componentless initial state")
    for row, reference in zip(states[1:], reversed(occurrences), strict=True):
        component = row["o"].FieldsValue["f10"]
        target = component.FieldsValue["f20"].FieldsValue["f08"].FieldsValue["f08"][0]["o"]
        require(target.FieldsValue["f44"] == reference.FieldsValue["f08"] and target.FieldsValue["f50"] is None and component.FieldsValue["f30"] == 203,
                "reverse configuration insertion context or chain stamp differs")
    specs = request["mates"] if "mates" in request else (request["mate"],)
    require(len(mates.RootsValue) == len(specs), "ordered authored mate count differs")
    ordered = []
    for index, (mate, spec) in enumerate(zip(mates.RootsValue, specs, strict=True)):
        wrappers = tuple(row["o"] for row in mate.FieldsValue["f410"])
        for wrapper, occurrence in zip(wrappers, occurrences, strict=True):
            chain = wrapper.FieldsValue["f58"].FieldsValue["f58"]
            target = chain.FieldsValue["f20"].FieldsValue["f08"].FieldsValue["f08"][0]["o"]
            require(chain.FieldsValue["owner"] is model and target is occurrence.FieldsValue["f4f8"], "ordered mate wrapper lost actual containing occurrence identity")
        require([reference.FieldsValue["f408"] for reference in occurrences] == [int(ordinal == spec["fixed_occurrence"]) for ordinal in range(2)], "actual fixed anchor differs")
        require([wrapper.FieldsValue["f78"] for wrapper in wrappers] == [2 * index, 2 * index + 1] and all(wrapper.FieldsValue["f74"] == mate.FieldsValue["f08"] for wrapper in wrappers), "wrapper ids or mate publication differ")
        row = {"class": mate.ClassValue.NameValue, "mate_id": mate.FieldsValue["f08"], "wrapper_ids": [wrapper.FieldsValue["f78"] for wrapper in wrappers]}
        if spec["kind"] == "distance":
            handle, = (value["o"] for value in mate.FieldsValue["f4b8"].FieldsValue["f850"])
            dimension = handle.FieldsValue["ff0"]
            require(dimension.FieldsValue["f50"] < mate.FieldsValue["f08"] and dimension.FieldsValue["f28"].FieldsValue["f58"] == spec["distance_m"], "ordered live distance dimension value or allocation differs")
            row["dimension_id"] = dimension.FieldsValue["f50"]
        ordered.append(row)
    entry, = (row["o"] for row in mgr_header.RootValue.FieldsValue["f08"]["items"])
    require(entry.FieldsValue["f50"] == model.FieldsValue["f1300"] + sum(reference.FieldsValue["f3f4"] for reference in occurrences) and entry.FieldsValue["f4c"] == sum(reference.FieldsValue["f3f0"] for reference in occurrences), "folded manager header target stamps differ")
    checks = {"actual_occurrence_and_directory_aliases": True, "ordered_mate_occurrence_backlinks": True, "reverse_configuration_insertion": True,
            "separate_componentless_state": True, "fixed_anchor": specs[0]["fixed_occurrence"], "manager_geometry_stamp": entry.FieldsValue["f50"], "manager_transform_stamp": entry.FieldsValue["f4c"],
            "direct_directory_slot": 4, "config_states": len(states), "config_map_counter": parent.ConfigValue.MapValue.CounterValue,
            "resolved_map_counter": parent.ResolvedValue.MapValue.CounterValue, "mates_map_base": mates.MapBase, "mates_map_terminal": mates.MapValue.CounterValue}
    if "mates" in request:
        checks["ordered_mates"] = ordered
    return checks


def main():
    built = REQUEST["build"]
    archives = {}
    for kind in ("assembly", "child"):
        data = b64decode(built[kind]["blob"], validate=True)
        require(len(data) == built[kind]["bytes"] and sha256(data).hexdigest() == built[kind]["sha256"], "generated artifact custody differs")
        archives[kind] = SldprtArchive.from_bytes(data)
    parent, mates, mgr_header, manager, parent_streams = roundtrips(archives["assembly"], True)
    child, _, _, _, child_streams = roundtrips(archives["child"], False)
    checks = inspect(parent, mates, mgr_header, manager, child, built, REQUEST["request"])
    return {"passed": True, "worker_pid": os.getpid(), "scope": "independent complete generated assembly and child typed stream preparation",
            "assembly": parent_streams, "child": child_streams, "round_trips": len(parent_streams) + len(child_streams), "checks": checks,
            "runtime_input_file_reads": len(AUDIT.DeniedReads), "native_acceptance": False, "public_writer_qualified": False}


print(json.dumps(main(), sort_keys=True, allow_nan=False))
