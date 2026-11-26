from argparse import ArgumentParser
from hashlib import sha256
from json import dumps
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from convert.adapters.solidworks.Archive.Header.HeaderFields import KHeaderVersion
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive


def replay_header(name, payload, version):
    root = ReadHeaderGraph(payload, version)
    if root.StartOffset != 0 or root.EndOffset != len(payload):
        raise ValueError(f"{name} root did not consume the complete stream")
    if WriteHeadGraph(root, version) != payload:
        raise ValueError(f"{name} changed after typed re-emission")
    return {
        "byte_count": len(payload),
        "sha256": sha256(payload).hexdigest(),
        "root_index": root.IndexValue,
    }


def check_document(document):
    original = document.read_bytes()
    archive = SldprtArchive.from_bytes(original, document)
    version = ContainerMo(archive.streams)
    if archive.format_version != 4 or version != KHeaderVersion:
        raise ValueError("standalone header replay requires format 4 and version 19000")
    names = ("Header2", "Contents/Config-0-ModelHeader")
    streams = {name: replay_header(name, archive.require(name), version) for name in names}
    if document.read_bytes() != original:
        raise ValueError("standalone header source changed during replay")
    return {
        "source_sha256": sha256(original).hexdigest(),
        "container_version": archive.format_version,
        "archive_version": version,
        "streams": streams,
    }


def main():
    parser = ArgumentParser(description="Check byte identity of standalone SW2026 headers")
    parser.add_argument("document", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    options = parser.parse_args()
    report = check_document(options.document)
    with options.report.open("x", encoding="utf-8") as output:
        output.write(dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
