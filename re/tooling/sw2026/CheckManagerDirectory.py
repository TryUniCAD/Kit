from argparse import ArgumentParser
from hashlib import sha256
from json import dumps, loads
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from convert.adapters.solidworks.Archive.CmgrHeader.ManagerSchemas import (
    KConfigHdrClass,
    KManagerClass,
)
from convert.adapters.solidworks.Archive.CmgrHeader.ReadMgrHdrMut import ReadMgrHdrMut
from convert.adapters.solidworks.Archive.CmgrHeader.WriteMgrHdrMut import WriteMgrHdrMut
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive


def author_directory(source):
    rows = []
    root = ArchiveNode(
        KManagerClass,
        {
            "f08": {"items": rows},
            "f60": source["saved_at"],
            "f68": source["sort_word"],
        },
    )
    for spec in source["rows"]:
        if spec is None:
            node = None
        elif spec == "root":
            node = root
        elif type(spec) is int:
            node = rows[spec]["o"]
        else:
            node = ArchiveNode(KConfigHdrClass, spec)
        rows.append({"o": node})
    return root


def replay_directory(payload, version):
    graph = ReadMgrHdrMut(payload, version)
    root = graph.RootValue
    if root.StartOffset != 0 or root.EndOffset != len(payload):
        raise ValueError("manager directory did not consume the complete stream")
    written, repeated = WriteMgrHdrMut(root, version)
    if written != payload or repeated.MapValue != graph.MapValue:
        raise ValueError("manager directory bytes or map changed on replay")
    entries = {entry.IndexValue: entry.EntryValue for entry in graph.MapValue.EntriesValue}
    rows = root.FieldsValue["f08"]
    row_indices = []
    for row in rows["items"]:
        child = row["o"]
        if entries.get(child.IndexValue) is not child:
            raise ValueError("manager directory row lost mapped identity")
        row_indices.append(child.IndexValue)
    return {
        "bytes": len(payload),
        "sha256": sha256(payload).hexdigest(),
        "archive_version": version,
        "root_index": root.IndexValue,
        "entry_indices": list(entries),
        "next_index": graph.MapValue.CounterValue,
        "row_count": rows["n"],
        "row_indices": row_indices,
        "saved_at": root.FieldsValue["f60"],
        "sort_word": root.FieldsValue["f68"],
        "schemas": graph.ReportValue["schema_calls"],
    }


def replay_container(path, expected_hash):
    original = path.read_bytes()
    digest = sha256(original).hexdigest()
    if digest != expected_hash:
        raise ValueError("manager directory fixture differs from the disclosed hash")
    archive = SldprtArchive.from_bytes(original, path)
    version = ContainerMo(archive.streams)
    if archive.format_version != 4 or version != 19000:
        raise ValueError("manager directory replay requires format 4 and version 19000")
    report = replay_directory(archive.require("Contents/CMgrHdr2"), version)
    if path.read_bytes() != original:
        raise ValueError("manager directory source changed during replay")
    report.update(source_sha256=digest, container_version=archive.format_version)
    return report


def main():
    parser = ArgumentParser(description="Check the ordinary SW2026 manager directory")
    parser.add_argument("mode", choices=("write", "read", "document"))
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--source-sha256")
    options = parser.parse_args()
    if options.mode == "write":
        source = loads(options.source.read_text(encoding="utf-8"))
        payload, _ = WriteMgrHdrMut(author_directory(source), 19000)
    else:
        if options.mode == "document":
            report = replay_container(options.source, options.source_sha256)
        else:
            report = replay_directory(options.source.read_bytes(), 19000)
        payload = dumps(report).encode("utf-8")
    with options.output.open("xb") as output:
        output.write(payload)


if __name__ == "__main__":
    main()
