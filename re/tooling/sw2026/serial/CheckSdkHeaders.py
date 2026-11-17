from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))
ARCHIVE = ROOT / "src/convert/adapters/solidworks/Archive"

from convert.adapters.solidworks.Archive.Header.HeaderFields import KHeaderVersion
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive


def digest(value):
    return hashlib.sha256(value).hexdigest()


def table_size(node):
    if node is None:
        return 0
    return len(node.FieldsValue["items"])


def codec_sources():
    paths = sorted((ARCHIVE / "Header").glob("*.py"))
    paths.append(ARCHIVE / "Reading/ReadNativeText.py")
    return {path.relative_to(ROOT).as_posix(): digest(path.read_bytes()) for path in paths}


def verify(path):
    original = path.read_bytes()
    archive = SldprtArchive.from_bytes(original, path)
    version = ContainerMo(archive.streams)
    if archive.format_version != 4 or version != KHeaderVersion:
        raise ValueError(f"{path.name} requires the current SOLIDWORKS header format")
    streams = {}
    for entry in archive.records:
        if entry.name != "Header2" and not entry.name.endswith("-ModelHeader"):
            continue
        root = ReadHeaderGraph(entry.data, version)
        encoded = WriteHeadGraph(root, version)
        if encoded != entry.data:
            raise ValueError(f"{path.name} {entry.name} differs after typed storage")
        fields = root.FieldsValue
        streams[entry.name] = {
            "sha256": digest(encoded), "bytes": len(encoded),
            "file_entries": table_size(fields["f30"]),
            "revision_logs": table_size(fields["f20"]),
            "self_file": fields["f38"] is not None,
            "bounds": fields["bbox"] is not None,
        }
    if "Header2" not in streams or path.read_bytes() != original:
        raise ValueError(f"{path.name} lacks the primary header or its input changed")
    return {"file": path.name, "sha256": digest(original), "streams": streams}


def main():
    parser = argparse.ArgumentParser(description="Record exact shared SDK header graph round trips")
    parser.add_argument("document", nargs="+", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    cases = [verify(path) for path in args.document]
    report = {
        "schema": "kit.sw2026.sdk-shared-header-graph.v1", "passed": True,
        "header_archive_version": KHeaderVersion,
        "document_count": len(cases), "stream_comparisons": sum(len(case["streams"]) for case in cases),
        "writer_output_count": 0, "native_application_runs": 0, "cases": cases,
        "codec_sources": codec_sources(),
    }
    with args.report.open("x", encoding="utf-8") as output:
        json.dump(report, output, indent=2)
        output.write("\n")
    print(json.dumps({"documents": report["document_count"], "header_streams": report["stream_comparisons"]}))


if __name__ == "__main__":
    main()
