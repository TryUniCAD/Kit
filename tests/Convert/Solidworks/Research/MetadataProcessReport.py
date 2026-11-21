from __future__ import annotations

from builtins import getattr as GetAttr
from hashlib import sha256 as HashBytes
from xml.etree.ElementTree import fromstring as ParseXml


# parent assertions need decoded semantic observations rather than constructor shaped success reports
def InspectResult(
    StreamData: dict[str, bytes], Records: dict[str, object]
) -> dict[str, object]:
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
        "log_names": {
            NameValue: [
                Entry["o"].f["f50"] for Entry in GetAttr(Record, "f")["f20"].f["items"]
            ]
            for NameValue, Record in Records.items()
            if NameValue == "Header2" or NameValue.startswith("Contents/")
        },
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
