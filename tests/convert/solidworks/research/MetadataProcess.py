from __future__ import annotations

from builtins import getattr as GetAttr, open as OpenFile
from codecs import lookup as FindCodec
from hashlib import sha256 as HashBytes
from importlib import import_module as ImportModule
from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath
from sys import addaudithook as AddAuditHook, argv as ArgValues, path as ImportPaths
from sys import stdin as InputStream
from typing import cast as CastValue
from xml.etree.ElementTree import fromstring as ParseXml

KRepoRoot = FilePath(ArgValues[1])
ImportPaths.insert(0, str(KRepoRoot))
ImportPaths.insert(0, str(KRepoRoot / "re" / "tooling" / "sw2026" / "serial"))
ImportPaths.insert(0, str(KRepoRoot / "re" / "tooling" / "sw2026"))

from tests.convert.solidworks.research.ConstructionGuard import BuildAudit

KAuditValue = BuildAudit(KRepoRoot / "re" / "tooling" / "sw2026" / "serial" / "defs")
AddAuditHook(KAuditValue.InspectEvent)

KMetadata = ImportModule("builders.Metadata")
KLoadRooted = ImportModule("Streams").load_rooted
KStoreRooted = ImportModule("Streams").store_rooted
KRegistry = ImportModule("Classes").registry()
KRequest = CastValue(list[dict[str, dict[str, object]]], LoadJson(InputStream.read()))
KCodecs = tuple(FindCodec(Value) for Value in ("utf-16-le", "utf-8", "latin-1"))


KAuditValue.BeginBuild()


def BuildStreams(InputData: dict[str, dict[str, object]]) -> dict[str, bytes]:
    return CastValue(
        dict[str, bytes],
        KMetadata.streams(
            registry=KRegistry,
            header2=KMetadata.header(**InputData["header2"]),
            model_headers={
                int(Index): KMetadata.header(**CastValue(dict[str, object], Values))
                for Index, Values in InputData["model_headers"].items()
            },
            biography_record=KMetadata.biography(),
            history_record=KMetadata.history(**InputData["history"]),
            keywords_data=KMetadata.keywords(**InputData["keywords"]),
        ),
    )


def DecodeStreams(StreamData: dict[str, bytes]) -> dict[str, object]:
    Records: dict[str, object] = {}
    for StreamName, BlobValue in StreamData.items():
        if StreamName == "swXmlContents/KeyWords":
            continue
        DocValue, Archive = KLoadRooted(BlobValue, KRegistry, 1, 19000)
        assert Archive.left() == 0 and not DocValue.tail
        assert len(DocValue.roots) == 1
        assert KStoreRooted(DocValue, KRegistry, 19000) == BlobValue
        Records[StreamName] = DocValue.roots[0]
    return Records


def InspectResult(StreamData: dict[str, bytes]) -> dict[str, object]:
    Records = DecodeStreams(StreamData)
    Header = GetAttr(Records["Header2"], "f")
    History = GetAttr(Records["_MO_VERSION_19000/History"], "f")
    XmlRoot = ParseXml(StreamData["swXmlContents/KeyWords"][1:])
    return {
        "sizes": {
            NameValue: len(BlobValue) for NameValue, BlobValue in StreamData.items()
        },
        "hashes": {
            NameValue: HashBytes(BlobValue).hexdigest()
            for NameValue, BlobValue in StreamData.items()
        },
        "next_id": Header["f08"],
        "header_owner": Header["fec"],
        "users": [Entry["s"] for Entry in Header["f10"].f["items"]],
        "log_ids": [Entry["o"].f["f48"] for Entry in Header["f20"].f["items"]],
        "models": {
            NameValue: GetAttr(Record, "f")["fec"]
            for NameValue, Record in Records.items()
            if NameValue.startswith("Contents/")
        },
        "biography_count": GetAttr(Records["_MO_VERSION_19000/Biography"], "f")["n"],
        "history_codes": [
            [Entry["st"]["f08"] for Entry in State["st"]["f38"].f["states"]]
            for State in History["states"]
        ],
        "history_user_indices": [
            State["st"]["f08"]["f0c"] for State in History["states"]
        ],
        "license_origin": History["f30"],
        "name": XmlRoot.attrib["Name"],
        "configs": [
            XmlNode.attrib["id"] for XmlNode in XmlRoot.findall("Configuration")
        ],
        "features": [
            XmlNode.attrib["Name"]
            for XmlNode in XmlRoot
            if XmlNode.tag != "Configuration"
        ],
        "dimensions": [XmlNode.text for XmlNode in XmlRoot.iter("Dimension")],
        "children": [
            XmlNode.attrib["DissectableChildren"]
            for XmlNode in XmlRoot
            if "DissectableChildren" in XmlNode.attrib
        ],
    }


def ProcessInput(InputData: dict[str, dict[str, object]]) -> dict[str, object]:
    Result: dict[str, object]
    try:
        Result = InspectResult(BuildStreams(InputData))
    except ValueError as ErrorInfo:
        Result = {"error": str(ErrorInfo)}
    try:
        with OpenFile("/metadata-donor-input.SLDPRT", "rb") as DonorStream:
            raise RuntimeError("forbidden donor open succeeded: " + DonorStream.name)
    except PermissionError:
        Result["read_blocked"] = True
    return Result


print(DumpJson([ProcessInput(InputData) for InputData in KRequest]))
