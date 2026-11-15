from __future__ import annotations

from builtins import open as OpenFile
from codecs import lookup as FindCodec
from hashlib import sha256 as HashBytes
from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath
from sys import addaudithook as AddAuditHook, argv as ArgValues, path as ImportPaths
from sys import stdin as InputStream
from typing import Any
from xml.etree.ElementTree import fromstring as ParseXml

KRepoRoot = FilePath(ArgValues[1])
ImportPaths.insert(0, str(KRepoRoot / "re" / "tooling" / "sw2026" / "serial"))
ImportPaths.insert(0, str(KRepoRoot / "re" / "tooling" / "sw2026"))

from Classes import registry as MakeRegistry
from Streams import load_rooted as LoadRooted, store_rooted as StoreRooted
from builders.Metadata import biography as MakeBiography, header as MakeHeader
from builders.Metadata import history as MakeHistory, keywords as MakeKeywords
from builders.Metadata import streams as MakeStreams

KRegistry = MakeRegistry()
KRequest = LoadJson(InputStream.read())
KCodecs = tuple(FindCodec(Value) for Value in ("utf-16-le", "utf-8", "latin-1"))


def DenyFiles(EventName: str, ArgsValue: tuple[Any, ...]) -> None:
    if EventName in ("open", "os.listdir", "os.scandir", "subprocess.Popen"):
        raise PermissionError("metadata construction cannot access runtime files")


AddAuditHook(DenyFiles)


def BuildStreams(InputData: dict[str, Any]) -> dict[str, bytes]:
    return MakeStreams(
        registry=KRegistry,
        header2=MakeHeader(**InputData["header2"]),
        model_headers={
            int(Index): MakeHeader(**Values)
            for Index, Values in InputData["model_headers"].items()
        },
        biography_record=MakeBiography(),
        history_record=MakeHistory(**InputData["history"]),
        keywords_data=MakeKeywords(**InputData["keywords"]),
    )


def DecodeStreams(StreamData: dict[str, bytes]) -> dict[str, Any]:
    Records = {}
    for StreamName, BlobValue in StreamData.items():
        if StreamName == "swXmlContents/KeyWords":
            continue
        DocValue, Archive = LoadRooted(BlobValue, KRegistry, 1, 19000)
        assert Archive.left() == 0 and not DocValue.tail
        assert len(DocValue.roots) == 1
        assert StoreRooted(DocValue, KRegistry, 19000) == BlobValue
        Records[StreamName] = DocValue.roots[0]
    return Records


def InspectResult(StreamData: dict[str, bytes]) -> dict[str, Any]:
    Records = DecodeStreams(StreamData)
    Header = Records["Header2"].f
    History = Records["_MO_VERSION_19000/History"].f
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
            NameValue: Record.f["fec"]
            for NameValue, Record in Records.items()
            if NameValue.startswith("Contents/")
        },
        "biography_count": Records["_MO_VERSION_19000/Biography"].f["n"],
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


def ProcessInput(InputData: dict[str, Any]) -> dict[str, Any]:
    try:
        Result = InspectResult(BuildStreams(InputData))
    except ValueError as ErrorInfo:
        Result = {"error": str(ErrorInfo)}
    try:
        OpenFile("/metadata-donor-input.SLDPRT", "rb")
    except PermissionError:
        Result["read_blocked"] = True
    return Result


print(DumpJson([ProcessInput(InputData) for InputData in KRequest]))
