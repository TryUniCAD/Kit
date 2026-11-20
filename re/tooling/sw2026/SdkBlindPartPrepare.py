from __future__ import annotations

from base64 import b64decode
from codecs import lookup
from hashlib import sha256
import json
from pathlib import Path
import sys
from xml.etree.ElementTree import fromstring

ROOT = Path(sys.argv[1])
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(ROOT / "re/tooling/sw2026")]

from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

AUDIT = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
sys.addaudithook(AUDIT.InspectEvent)

from SdkBlindPartChecks import driving_depth, geometry, name, node, require, self_file
from convert.adapters.solidworks.Archive.Bodies.BodyReport import GetBodyReport
from convert.adapters.solidworks.Archive.Bodies.BodyUsage import BodyUsage
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Archive.CmgrHeader.ReadMgrHeader import ReadMgrHeader
from convert.adapters.solidworks.Archive.CmgrHeader.WriteMgrHeader import WriteMgrHeader
from convert.adapters.solidworks.Archive.Config.MakeLinkContext import MakeLinkContext
from convert.adapters.solidworks.Archive.Config.ReadConfigMut import ReadConfigMut
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Construction.Metadata.FrameKeywords import FrameKeywords
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectBlind import ProjectBlind
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectPlain import ProjectPlain
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadLineLoop import ReadLineLoop
from convert.adapters.solidworks.Archive.Definition.ReadModelDef import ReadModelDef
from convert.adapters.solidworks.Archive.Definition.WriteModelDef import WriteModelDef
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.History.ReadHistMut import ReadHistMut
from convert.adapters.solidworks.Archive.History.WriteHistMut import WriteHistMut
from convert.adapters.solidworks.Archive.Resolved.ReadResolvedMut import ReadResolvedMut
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import SldprtArchive
from interchange.document.Validation.DocumentAssemblyValidate import GetAssemblyErrs
from interchange.document.Validation.DocumentFeatureValidate import GetFeatureErrs
from interchange.document.Validation.DocumentReferenceValidate import GetRefErrors
from interchange.serialization.Deserialize import FromData

CODECS = tuple(lookup(value) for value in ("utf-16-le", "utf-8", "latin-1"))
REQUEST = json.load(sys.stdin)
PROFILE = sys.argv[2] if len(sys.argv) == 3 else "rectangle"
AUDIT.BeginBuild()


def keyword_graph(data, built, request, features, configuration):
    require(data.startswith(b'\x86<?xml version="1.0" encoding="UTF-8"?>\r\n') and data.endswith(b"\r\n"),
            "keywords lost native computed framing")
    root = fromstring(data[1:])
    require(root.tag == "Keywords" and root.attrib == {"id": str(request["provenance"]["modified_at"]), "Name": built["name"]},
            "keywords lost neutral document identity")
    rows = list(root)
    require(len(rows) == len(features) + 1 and rows[0].tag == "Configuration" and
            rows[0].attrib["Name"] == name(configuration) and rows[0].attrib["id"] == str(configuration.FieldsValue["f08"]),
            "keywords lost actual configuration identity")
    for row, feature in zip(rows[1:], features, strict=True):
        require(row.attrib["Name"] == name(feature) and row.attrib["id"] == str(feature.FieldsValue["f08"]),
                "keyword feature identity differs from actual native graph")
    require(rows[-2].tag == "Sketch" and rows[-1].tag == "Extrusion" and len(rows[-1]) == 1,
            "keyword sketch and boss topology differs")
    dimension = rows[-1][0]
    scale = {"mm": 0.001, "m": 1.0, "in": 0.0254}[request["document_units"]["length_unit"]]
    require(dimension.tag == "Dimension" and dimension.attrib["Name"] == "D1" and
            float(dimension.text) == built["depth_m"] / scale,
            "keywords lost actual driving depth presentation")
    return FrameKeywords(root, False)


def main():
    built, request = REQUEST["build"], REQUEST["request"]["settings"]
    document = FromData(REQUEST["request"]["document"])
    require(PROFILE in ("rectangle", "polygon"), "unknown complete part profile")
    plan = ProjectBlind(document, ReadLineLoop) if PROFILE == "polygon" else ProjectPlain(document)
    require(plan.NameValue == built["name"] and plan.DepthValue == built["depth_m"] and
            list(map(list, plan.VerticesValue)) == built["vertices_m"], "prepared geometry was not derived from the actual neutral input")
    blob = b64decode(built["blob"], validate=True)
    require(len(blob) == built["bytes"] and sha256(blob).hexdigest() == built["sha256"], "artifact custody differs")
    archive = SldprtArchive.from_bytes(blob)
    buffers = {record.name: record.data for record in archive.records}
    require(buffers.keys() == built["streams"].keys() and len(buffers) == 10, "complete native stream set differs")
    for stream, data in buffers.items():
        row = built["streams"][stream]
        require(data == b64decode(row["data"], validate=True) and len(data) == row["bytes"] and sha256(data).hexdigest() == row["sha256"],
                "complete stream custody differs: " + stream)
    header = ReadHeaderGraph(buffers["Contents/Config-0-ModelHeader"], 19000)
    top = ReadHeaderGraph(buffers["Header2"], 19000)
    config = ReadConfigMut(buffers["Contents/Config-0"], 19000, header)
    manager = ReadCmgrMut(buffers["Contents/CMgr"], 19000)
    context = MakeLinkContext(config, manager)
    resolved = ReadResolvedMut(buffers["Contents/Config-0-ResolvedFeatures"], 19000, config.MapValue, context)
    root = node(config.RootValue, "moPart_c")
    require(name(root) == built["name"] and root.FieldsValue["f08"] == built["root_id"], "actual model identity differs")
    require(header.FieldsValue["f08"] == top.FieldsValue["f08"] == built["next_id"] and header.FieldsValue["fec"] == 1 and top.FieldsValue["fec"] == 0,
            "header allocator or presence state differs")
    require(root.FieldsValue["f2f8"] is None, "fresh model acquired an unproved configuration-manager wire backlink")
    configuration = node(manager.RootValue.FieldsValue["f360"], "moPartConfiguration_c")
    require(configuration is manager.RootValue.FieldsValue["f368"] is manager.RootValue.FieldsValue["f370"]["items"][0]["o"] and
            configuration.FieldsValue["f08"] == 0 and configuration.FieldsValue["f85c"] == built["next_id"] - 1,
            "actual manager selection local identity or allocation progress differs")
    features = resolved.RootsValue
    require(len(features) == built["feature_count"] == 19 and len({id(value) for value in features}) == 19,
            "complete feature graph ownership differs")
    require(root.FieldsValue["f1e0"] is features[8], "configuration and resolved environment aliases differ")
    profile = node(features[-2], "moProfileFeature_c")
    boss = node(features[-1], "moExtrusion_c")
    require(name(profile) == plan.SketchName and name(boss) == plan.FeatureName, "neutral feature identities differ")
    require(boss.FieldsValue["f60"]["list"]["items"][0]["o"] is profile, "actual boss dependency differs")
    support = node(profile.FieldsValue["pd_f78"], "moCompRefPlane_c")
    require(node(support.FieldsValue["f58"], "moUnitComponent_c").FieldsValue["owner"] is root, "actual support model alias differs")
    geometry_checks = geometry(profile.FieldsValue["pd_f80"], built["vertices_m"])
    depth_checks = driving_depth(boss, built["depth_m"], built["dimension_ids"][0])
    self_checks = [self_file(value, request, built["name"], name(configuration)) for value in (header, top)]
    prefix = {entry.IndexValue: entry.EntryValue for entry in config.MapValue.EntriesValue}
    require(resolved.MapBase == config.MapValue.CounterValue == built["config_map_counter"] and
            resolved.MapValue.CounterValue == built["resolved_map_counter"] and
            all(entry.EntryValue is prefix[entry.IndexValue] for entry in resolved.MapValue.EntriesValue if entry.IndexValue in prefix),
            "resolved graph lost exact configuration map aliases or counters")
    config_bytes, repeated = WriteConfigMut(root, 19000, header)
    cmgr_usage = BodyUsage()
    cmgr_bytes = WriteCmgrMut(manager.RootValue, 19000, UsageValue=cmgr_usage)
    resolved_bytes, repeated_resolved = WriteResolMut(features, resolved.ExtraFields, 19000, repeated.MapValue, context)
    mgr_header = ReadMgrHeader(buffers["Contents/CMgrHdr2"], 19000)
    mgr_bytes, repeated_mgr = WriteMgrHeader(mgr_header.RootValue, 19000)
    definition = ReadModelDef(buffers["Contents/Definition"], 19000)
    def_bytes = WriteModelDef(definition.GraphValue)
    bio = ReadHistMut(buffers["_MO_VERSION_19000/Biography"], 19000)
    history = ReadHistMut(buffers["_MO_VERSION_19000/History"], 19000)
    bio_bytes, repeated_bio = WriteHistMut(bio.RootValue, 19000)
    hist_bytes, repeated_hist = WriteHistMut(history.RootValue, 19000)
    actual = {"Header2": WriteHeadGraph(top, 19000), "Contents/Config-0-ModelHeader": WriteHeadGraph(header, 19000),
              "Contents/Config-0": config_bytes, "Contents/CMgr": cmgr_bytes, "Contents/CMgrHdr2": mgr_bytes,
              "Contents/Config-0-ResolvedFeatures": resolved_bytes, "Contents/Definition": def_bytes.OutputValue,
              "_MO_VERSION_19000/Biography": bio_bytes, "_MO_VERSION_19000/History": hist_bytes,
              "swXmlContents/KeyWords": keyword_graph(buffers["swXmlContents/KeyWords"], built, request, features, configuration)}
    comparisons = {stream: {"bytes": len(data), "sha256": sha256(data).hexdigest(), "byte_identity": data == buffers[stream]}
                   for stream, data in actual.items()}
    require(all(row["byte_identity"] for row in comparisons.values()), "complete typed preparation changed generated native streams")
    usage = {"config_load": config.ReportValue, "config_store": repeated.ReportValue,
             "manager_load": manager.ReportValue, "manager_store": GetBodyReport(cmgr_usage),
             "resolved_load": resolved.ReportValue, "resolved_store": repeated_resolved.ReportValue,
             "manager_header_load": mgr_header.ReportValue, "manager_header_store": repeated_mgr.ReportValue,
             "definition_load": GetBodyReport(definition.UsageValue), "definition_store": GetBodyReport(def_bytes.UsageValue),
             "biography_load": bio.ReportValue, "biography_store": repeated_bio.ReportValue,
             "history_load": history.ReportValue, "history_store": repeated_hist.ReportValue}
    require(all(row["completed"] and not row["missing_schemas"] and not row["provisional_schemas"] for row in usage.values()),
            "complete native preparation reached incomplete grammar")
    imports = sorted(value for value, module in tuple(sys.modules.items())
                     if str(getattr(module, "__file__", "")).startswith(str(ROOT / "re") + "/") and value not in ("__main__", "SdkBlindPartChecks"))
    require(not imports, "SDK-only preparation imported research implementation: " + repr(imports))
    return {"passed": True, "scope": "separate complete SDK part preparation and typed stream serialization",
            "artifact_sha256": sha256(blob).hexdigest(), "streams": comparisons, "usage": usage,
            "geometry": geometry_checks, "driving_depth": depth_checks, "self_file": self_checks,
            "feature_count": len(features), "actual_profile_dependency": True, "actual_support_owner": True,
            "actual_configuration_map_aliases": True, "config_map_counter": config.MapValue.CounterValue,
            "resolved_map_counter": resolved.MapValue.CounterValue, "runtime_input_file_reads": len(AUDIT.DeniedReads),
            "sdk_runtime_research_imports": len(imports), "native_acceptance": False, "public_writer_qualified": False}


print(json.dumps(main(), sort_keys=True, allow_nan=False))
