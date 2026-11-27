from hashlib import sha256
import json
from pathlib import Path
from subprocess import check_output
import sys

from convert.Geometry.Parasolid import (
    CollectPartTopo,
    MakePartRanks,
    ParaHeaderData,
    ReadBrepResult,
    ScanPartRecords,
)
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Parasolid import DecodePartition


def digest(data):
    return sha256(data).hexdigest()


def inspect(source, expected_archive, expected_payload):
    raw = source.read_bytes()
    if digest(raw) != expected_archive:
        raise ValueError("unexpected archive bytes")
    archive = SldprtArchive.from_bytes(raw, source.name)
    stream = archive.Require("Contents/Config-0-Partition")
    payloads = DecodePartition(stream)
    (active,) = (item for item in payloads if item.kind == "partition")
    if digest(active.data) != expected_payload:
        raise ValueError("unexpected active payload bytes")
    header = ParaHeaderData(active.data)
    if header is None or header.schema != "SCH_3701250_37102_13006":
        raise ValueError("unexpected active payload profile")
    scanned = ScanPartRecords(
        active.data[header.body_offset :], TerminalFinVertices=True
    )
    if scanned is None:
        raise ValueError("generic table scan refused")
    faces, endpoints, curves, coedge_edges, _, edges, vertices, _, _, synthetic, *_ = (
        CollectPartTopo(scanned)
    )
    orders, _ = MakePartRanks(scanned, faces, edges, vertices, set(curves.values()))
    missing = [
        key
        for key in orders[5]
        if key not in scanned.vertex_uses and key not in synthetic
    ]
    model, reason = ReadBrepResult(active.data)
    if source.read_bytes() != raw:
        raise ValueError("source bytes changed in custody")
    return {
        "archive_sha256": expected_archive,
        "active_sha256": expected_payload,
        "active_header_bytes": header.body_offset,
        "partition_member_sha256": digest(stream),
        "frames": [
            {"kind": item.kind, "sha256": digest(item.data), "size": len(item.data)}
            for item in payloads
        ],
        "old_model_available": model is not None,
        "old_reason": reason,
        "scanned_vertex_attributes": sorted(scanned.vertex_uses),
        "used_vertex_attributes": list(orders[5]),
        "missing_vertex_use": missing,
        "edges_involving_missing_vertex": [
            {
                "edge_attribute": edge,
                "carrier_attribute": curves.get(edge),
                "edge_scanner_offset": scanned.edge_uses[edge].offset,
                "endpoints": pair,
                "fins": [
                    {
                        "attribute": fin,
                        "scanner_offset": scanned.coedges[fin].offset,
                        "stored_vertex": scanned.coedges[fin].references[4],
                        "mate": scanned.coedges[fin].references[5],
                    }
                    for fin in sorted(coedge_edges)
                    if coedge_edges[fin] == edge
                ],
            }
            for edge, pair in sorted(endpoints.items())
            if set(pair).intersection(missing)
        ],
    }


def main():
    sdk, source, output = (Path(arg).resolve() for arg in sys.argv[1:4])
    src_tree = (
        check_output(("git", "-C", str(sdk), "rev-parse", "HEAD:src")).decode().strip()
    )
    if src_tree != "3739be2f567a3285dd3dc725be9d0d07865a7b18":
        raise ValueError("unexpected SDK source tree")
    if check_output(("git", "-C", str(sdk), "status", "--porcelain", "--", "src")):
        raise ValueError("working SDK source differs from tree")
    import convert

    if not Path(convert.__file__).resolve().is_relative_to(sdk / "src"):
        raise ValueError("unexpected SDK import root")
    finding = inspect(source, *sys.argv[4:6])
    receipt = {
        "schema": "kit.research.p03-legacy-vertex-boundary.v1",
        "sdk_source_tree": src_tree,
        "method_sha256": digest(Path(__file__).read_bytes()),
        "finding": finding,
        "public_reads": 0,
        "native_launches": 0,
    }
    with output.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(receipt, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(receipt, sort_keys=True))


if __name__ == "__main__":
    main()
