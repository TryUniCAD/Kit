from argparse import ArgumentParser
from hashlib import sha256
from json import dumps, loads
from pathlib import Path
import sys
from xml.etree.ElementTree import Comment, Element, ProcessingInstruction, QName, SubElement

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from convert.adapters.solidworks.Archive.Construction.Metadata.FrameKeywords import (
    FrameKeywords,
)
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KeywordsStream
from convert.adapters.solidworks.Core.Native import ParseXml


def author_frame(source):
    root = Element(source["root"], {"id": "17", "Name": source["name"]})
    root.tail = source.get("root_tail")
    SubElement(
        root,
        "Configuration",
        {"id": "0", "Name": "Default", "Type": "ConfigurationManager", "Material": ""},
    )
    feature = SubElement(
        root, "Feature", {"id": "7", "Name": "Sketch1", "Type": "ProfileFeature"}
    )
    dimension = SubElement(feature, source.get("child_tag", "Dimension"), {"Name": "D1"})
    dimension.text = source["text"]
    dimension.tail = source["tail"]
    markup = source.get("markup")
    if markup == "comment":
        feature.append(Comment("authored\r />"))
    elif markup == "instruction":
        feature.append(ProcessingInstruction("example", "authored\r />"))
    qualified = source.get("qualified")
    if qualified is not None:
        name = "{urn:kit:keyword}Native"
        SubElement(root, QName(name) if qualified == "object" else name)
    if source.get("literal_namespace"):
        root.set("xmlns:kit", "urn:kit:declared")
        feature.set("xml:lang", "en")
        feature.set("kit:role", "feature")
    if source.get("namespace_shadow"):
        feature.set("xmlns:ns0", "urn:kit:other")
        SubElement(feature, QName("{urn:kit:keyword}Native"))
    return FrameKeywords(root, source["compact"])


def describe_frame(payload):
    root = ParseXml(payload)
    dimension = root.find("./Feature/Dimension")
    if dimension is None:
        raise ValueError("authored keyword dimension is missing")
    return {
        "root": root.tag,
        "name": root.get("Name"),
        "text": dimension.text,
        "tail": dimension.tail,
    }


def replay_document(path, expected_hash, mode):
    original = path.read_bytes()
    digest = sha256(original).hexdigest()
    if digest != expected_hash:
        raise ValueError("keyword fixture differs from its disclosed hash")
    archive = SldprtArchive.from_bytes(original, path)
    version = ContainerMo(archive.streams)
    if archive.format_version != 4 or version != 19000:
        raise ValueError("keyword replay requires format 4 and archive version 19000")
    payload = archive.require(KeywordsStream)
    root = ParseXml(payload)
    if FrameKeywords(root, mode == "compact") != payload:
        raise ValueError("keyword framing changed disclosed stream bytes")
    if path.read_bytes() != original:
        raise ValueError("keyword fixture changed during replay")
    return {
        "source_sha256": digest,
        "stream_sha256": sha256(payload).hexdigest(),
        "byte_count": len(payload),
        "container_version": archive.format_version,
        "archive_version": version,
        "empty_tags": mode,
    }


def main():
    parser = ArgumentParser(description="Check SOLIDWORKS KeyWords XML framing")
    parser.add_argument("mode", choices=("read", "write", "document"))
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--source-sha256")
    parser.add_argument("--empty-tags", choices=("compact", "spaced"))
    options = parser.parse_args()
    if options.mode == "write":
        payload = author_frame(loads(options.source.read_text(encoding="utf-8")))
    elif options.mode == "read":
        payload = dumps(describe_frame(options.source.read_bytes())).encode("utf-8")
    else:
        if options.source_sha256 is None or options.empty_tags is None:
            parser.error("document replay requires the source hash and empty tag mode")
        report = replay_document(options.source, options.source_sha256, options.empty_tags)
        payload = dumps(report).encode("utf-8")
    with options.output.open("xb") as output:
        output.write(payload)


if __name__ == "__main__":
    main()
