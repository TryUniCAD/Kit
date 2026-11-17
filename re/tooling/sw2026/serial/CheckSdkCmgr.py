from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from convert.adapters.solidworks.Archive.Bodies.BodyReport import GetBodyReport
from convert.adapters.solidworks.Archive.Bodies.BodyUsage import BodyUsage
from convert.adapters.solidworks.Archive.Cmgr.ProjectCmgrRows import ProjectCmgrRows
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive


def check(path):
    source = path.read_bytes()
    archive = SldprtArchive.from_bytes(source)
    version = ContainerMo(archive.streams)
    data = archive.require("Contents/CMgr")
    loaded, stored = BodyUsage(), BodyUsage()
    graph = ReadCmgrMut(data, version, UsageValue=loaded)
    encoded = WriteCmgrMut(graph.RootValue, version, UsageValue=stored)
    if encoded != data:
        offset = next((index for index, (left, right) in enumerate(zip(data, encoded)) if left != right), min(len(data), len(encoded)))
        raise ValueError(f"SDK CMgr differs at {offset}, lengths {len(data)} and {len(encoded)}")
    return {
        "file": path.name, "source_sha256": hashlib.sha256(source).hexdigest(),
        "source_bytes": len(source), "stream": "Contents/CMgr", "archive_version": version,
        "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
        "output_sha256": hashlib.sha256(encoded).hexdigest(),
        "byte_identity_passed": True, "map_base": 1,
        "map_counter": graph.MapValue.CounterValue,
        "configuration_metadata": ProjectCmgrRows(graph.RootValue),
        "load": GetBodyReport(loaded), "store": GetBodyReport(stored),
    }


def main():
    parser = argparse.ArgumentParser(description="Check the shared SDK ordinary typed CMgr graph")
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    if args.report.exists():
        raise ValueError("report path must be unused")
    rows = [check(path) for path in args.files]
    report = {
        "schema": "kit.sw2026.sdk-cmgr-graph.v1", "passed": True,
        "files": rows, "public_full_linked_graph": False,
        "native_application_runs": 0, "writer_native_acceptance": False,
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "implementation": [
            {"file": str(path.relative_to(root)), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
            for root in (Path(__file__).resolve().parents[4],)
            for folder in (root / "src/convert/adapters/solidworks/Archive",)
            for path in sorted(folder.rglob("*.py"))
        ],
    }
    with args.report.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")
    print(f"{len(rows)} SDK CMgr graphs byte-identical")


if __name__ == "__main__":
    main()
