from __future__ import annotations

from base64 import b64encode
from codecs import lookup
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import sys
from xml.etree.ElementTree import fromstring


ROOT = Path(sys.argv[1])
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

AUDIT = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
sys.addaudithook(AUDIT.InspectEvent)

from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Archive.CmgrHeader.ReadMgrHdrMut import ReadMgrHdrMut
from convert.adapters.solidworks.Archive.CmgrHeader.WriteMgrHdrMut import WriteMgrHdrMut
from convert.adapters.solidworks.Archive.Config.MakeLinkContext import MakeLinkContext
from convert.adapters.solidworks.Archive.Config.ReadConfigMut import ReadConfigMut
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Definition.ReadModelDef import ReadModelDef
from convert.adapters.solidworks.Archive.Definition.WriteModelDef import WriteModelDef
from convert.adapters.solidworks.Archive.Construction.Metadata.FrameKeywords import FrameKeywords
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.History.ReadHistMut import ReadHistMut
from convert.adapters.solidworks.Archive.History.WriteHistMut import WriteHistMut
from convert.adapters.solidworks.Archive.Resolved.ReadResolvedMut import ReadResolvedMut
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Preparation.PrepareNative import PrepareNative
from convert.adapters.solidworks.Core.Writing import EmitNativeMut
from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
from interchange.document.Models.DocumentModel import CadDocument
from interchange.document.Validation.DocumentAssemblyValidate import GetAssemblyErrs
from interchange.document.Validation.DocumentFeatureValidate import GetFeatureErrs
from interchange.document.Validation.DocumentReferenceValidate import GetRefErrors
from interchange.serialization.Deserialize import FromData


CODECS = tuple(lookup(name) for name in ("utf-16-le", "utf-8", "latin-1"))
REQUEST = json.load(sys.stdin)
AUDIT.BeginBuild()


def require(value, message):
    if not value:
        raise ValueError(message)


def typed_readback(candidate, destination):
    archive = SldprtArchive.from_bytes(candidate.BytesValue)
    streams = {record.name: record.data for record in archive.records}
    require(len(streams) == 10 and streams == candidate.StreamsValue, "complete candidate stream mapping differs")
    head_name = "Contents/Config-0-ModelHeader"
    config_name = "Contents/Config-0"
    resolved_name = "Contents/Config-0-ResolvedFeatures"
    head = ReadHeaderGraph(streams[head_name], 19000)
    top = ReadHeaderGraph(streams["Header2"], 19000)
    manager = ReadCmgrMut(streams["Contents/CMgr"], 19000)
    config = ReadConfigMut(streams[config_name], 19000, head)
    context = MakeLinkContext(config, manager)
    resolved = ReadResolvedMut(streams[resolved_name], 19000, config.MapValue, context)
    definition = ReadModelDef(streams["Contents/Definition"], 19000)
    preference = definition.GraphValue.DocumentValue.FieldsValue
    require(
        [preference[key] for key in ("fa58", "fa5c", "fa60", "fa64", "fa90", "f1688")] == [26, 4, 25, 1, 0, 1000.0],
        "pinned new-document preference mapping differs",
    )
    for header in (head, top):
        referral = header.FieldsValue["f38"].FieldsValue
        path = referral["shared"]["h18"].FieldsValue["value"]
        require(path.TextValue == destination and referral["f60"] == REQUEST["written_at"], "native path or save event differs")
    cmgr_header = ReadMgrHdrMut(streams["Contents/CMgrHdr2"], 19000)
    require(cmgr_header.RootValue.FieldsValue["f60"] == REQUEST["written_at"], "typed manager save event differs")
    biography = ReadHistMut(streams["_MO_VERSION_19000/Biography"], 19000)
    history = ReadHistMut(streams["_MO_VERSION_19000/History"], 19000)
    keywords = fromstring(streams["swXmlContents/KeyWords"][1:])
    require(keywords.get("Name") == candidate.PlanValue.NameValue
            and keywords.get("id") == str(REQUEST["written_at"])
            and len(keywords) == 20
            and keywords[-1][0].get("Name") == "D1", "keyword identity or feature count differs")
    comparisons = {
        head_name: WriteHeadGraph(head, 19000),
        "Header2": WriteHeadGraph(top, 19000),
        "Contents/CMgr": WriteCmgrMut(manager.RootValue, 19000),
        "Contents/CMgrHdr2": WriteMgrHdrMut(cmgr_header.RootValue, 19000)[0],
        config_name: WriteConfigMut(config.RootValue, 19000, head)[0],
        resolved_name: WriteResolMut(resolved.RootsValue, resolved.ExtraFields, 19000, config.MapValue, context)[0],
        "Contents/Definition": WriteModelDef(definition.GraphValue).OutputValue,
        "_MO_VERSION_19000/Biography": WriteHistMut(biography.RootValue, 19000)[0],
        "_MO_VERSION_19000/History": WriteHistMut(history.RootValue, 19000)[0],
        "swXmlContents/KeyWords": FrameKeywords(keywords, False),
    }
    require(all(streams[name] == data for name, data in comparisons.items()), "typed readback changed a load-critical stream")
    return {
        name: {"sha256": sha256(data).hexdigest(), "bytes": len(data), "typed_roundtrip": name in comparisons}
        for name, data in streams.items()
    }


def main():
    document = FromData(REQUEST["document"])
    require(type(document) is CadDocument, "expected a concrete neutral document")
    written = REQUEST["written_at"]
    settings = WriteOptions(values={"final_destination": REQUEST["destination"]})
    buffer = BytesIO()
    candidate = PrepareNative(document, buffer, written, settings)
    require(candidate.ManagerHeader.FieldsValue["f60"] == written, "default writer event differs")
    EmitNativeMut.ReadTime = lambda: written
    writer = SldprtWriter()
    require(writer.supports(document, buffer), "default writing rejected the admitted neutral graph")
    result = writer.write(document, buffer, settings)
    require(result.path is None and result.bytes_written == len(candidate.BytesValue)
            and buffer.getvalue() == candidate.BytesValue, "public writer implementation used a different preparation path")
    streams = typed_readback(candidate, REQUEST["expected_locator"])
    require(not AUDIT.DeniedReads, "the writer read an input file")
    return {"passed": True, "blob": b64encode(candidate.BytesValue).decode(),
            "sha256": sha256(candidate.BytesValue).hexdigest(), "bytes": len(candidate.BytesValue),
            "streams": streams, "runtime_reads": len(AUDIT.DeniedReads), "native_acceptance": False}


print(json.dumps(main(), sort_keys=True, allow_nan=False))
