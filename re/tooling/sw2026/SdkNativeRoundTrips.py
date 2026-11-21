from hashlib import sha256
from xml.etree.ElementTree import fromstring, tostring

from convert.adapters.solidworks.Archive.Bodies.BodyReport import GetBodyReport
from convert.adapters.solidworks.Archive.Bodies.BodyUsage import BodyUsage
from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.CmgrHeader.ReadMgrHeader import ReadMgrHeader
from convert.adapters.solidworks.Archive.CmgrHeader.WriteMgrHeader import WriteMgrHeader
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Definition.ReadModelDef import ReadModelDef
from convert.adapters.solidworks.Archive.Definition.WriteModelDef import WriteModelDef
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.History.ReadHistMut import ReadHistMut
from convert.adapters.solidworks.Archive.History.WriteHistMut import WriteHistMut
from convert.adapters.solidworks.Archive.Mates.ReadMatesMut import ReadMatesMut
from convert.adapters.solidworks.Archive.Mates.WriteMatesMut import WriteMatesMut
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink


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
    manager_header = ReadMgrHeader(streams["Contents/CMgrHdr2"], 19000)
    actual["Contents/CMgrHdr2"], repeated = WriteMgrHeader(manager_header.RootValue, 19000)
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
