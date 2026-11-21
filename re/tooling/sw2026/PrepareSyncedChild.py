from __future__ import annotations

from ntpath import basename, isabs
from xml.etree import ElementTree

from PrepareAssemblySources import XML_MIRRORS
from PrepareCurveCorpus import MAX_DECODED, MAX_FILE, MAX_STREAM, binary_redaction, digest, xml_redaction
from PrepareSavedCircles import private_summary, require


MODEL = "http://www.solidworks.com/sw2003/schema}swModel"
FEATURES = "swXmlContents/Features"


def child_archive(api, raw, name, privacy):
    archive = api.SldprtArchive.FromBytes(raw, name, SizeLimit=MAX_DECODED)
    require({key.split("/", 1)[0] for key in archive.streams if key.startswith("_MO_VERSION_")} == {"_MO_VERSION_19000"}, "unexpected child format")
    entries, streams, ledger, previews = [], [], [], []
    count = 0
    for item in archive.records:
        require(not privacy.private(item.name) and len(item.data) <= MAX_STREAM, "child stream name or size is invalid")
        count += len(item.data)
        require(count <= MAX_DECODED, "child exceeds native stream bound")
        if item.name.endswith(".xml") or item.name in XML_MIRRORS:
            extra = tuple((stream, "http://www.solidworks.com/sw2003/schema}swFile", "swPath") for stream in XML_MIRRORS)
            if item.name == FEATURES:
                tree = ElementTree.fromstring(item.data)
                paths = [node.get("swName", "") for node in tree.iter("{" + MODEL) if privacy.private(node.get("swName", ""))]
                require(len(paths) == 1 and isabs(paths[0]) and basename(paths[0]) == "CohortChild.SLDPRT", "private child model name is not the owned absolute path")
                extra += ((FEATURES, MODEL, "swName"),)
            clean, changes, spans = xml_redaction(item.name, item.data, privacy, additional_metadata_properties=(("docProps/ISolidWorksInformation.xml", "SW-Folder Name"),), additional_metadata_attributes=extra)
        else:
            clean, changes = binary_redaction(item.name, item.data, privacy, additional_metadata_streams=("Contents/CMgr", "Contents/Config-0", "Contents/Config-0-ResolvedFeatures", "SwDocContentMgr/SwDocContentMgrInfo"))
            spans = []
        require(len(clean) == len(item.data), "child metadata transformation changed a field width")
        if privacy.scan(clean, spans):
            raise ValueError(f"unclassified private child context: {name}/{item.name}; {private_summary(clean, privacy)}")
        covered = {offset for row in changes for offset in range(row["offset"], row["offset"] + row["bytes"])}
        require(all(a == b or index in covered for index, (a, b) in enumerate(zip(item.data, clean, strict=True))), "unrecorded child metadata change")
        entries.append((item.name, clean))
        streams.append({"name": item.name, "bytes": len(clean), "source_sha256": digest(item.data), "sha256": digest(clean), "privacy_operations": len(changes)})
        ledger.extend({"stream": item.name, **row} for row in changes)
        if item.name == "PreviewPNG":
            require(clean.startswith(b"\x89PNG\r\n\x1a\n"), "unexpected child preview encoding")
            previews.append((name + ".png", clean))
    output = api.BuildSldprt(entries, Template=raw)
    require(len(output) <= MAX_FILE, "prepared child exceeds its fixture size bound")
    return output, streams, ledger, previews
