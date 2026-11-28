from argparse import ArgumentParser
from hashlib import sha256
from json import dumps, loads
from pathlib import Path, PureWindowsPath

from .Allocate import require
from .CheckAttachment import CASE_NAME, make_pair
from convert.Geometry.Parasolid import DecodePartData
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KPartitionStream
from para.Partition import read_partition


ORIGINAL_ATTACHMENT = "OriginalAttachment"
CORRECTED_ATTACHMENT = "CorrectedAttachment"


def digest(data):
    return sha256(data).hexdigest()


def verify_anchors(before, after):
    original, corrected = (read_partition(data) for data in (before, after))
    require(original.root == corrected.root and original.history == corrected.history, "partition history changed")
    after_nodes = {node.index: node.fields for node in corrected.nodes}
    edits = []
    for old, new in zip(original.nodes, corrected.nodes, strict=True):
        require((old.index, old.kind) == (new.index, new.kind), "active transmit indices or order changed")
        if old.kind != 16:
            require(old.fields == new.fields, "a non-edge record changed")
            continue
        a, b = (row.fields["halfedge"] for row in (old, new))
        require((old.fields | {"halfedge": b}) == new.fields, "another edge field changed")
        anchor = after_nodes[b]
        mate = after_nodes[anchor["other"]]
        start, end = (after_nodes[after_nodes[fin["vertex"]]["point"]]["pvec"] for fin in (mate, anchor))
        line = after_nodes[new.fields["curve"]]
        require(anchor["sense"] == line["sense"] == "+"
                and sum((finish - begin) * direction for begin, finish, direction in zip(start, end, line["direction"], strict=True)) > 0,
                "edge anchor disagrees with the authored line direction")
        if a != b:
            require(after_nodes[a]["other"] == b and after_nodes[a]["sense"] == "-", "edge anchor change did not select its forward mate")
            edits.append({"edge_transmit_index": old.index, "field": "halfedge", "from": a, "to": b})
    require(len(edits) == 5, "expected five anchor changes in the frozen design")
    original_frame, original_delta = DecodePartData(before)
    corrected_frame, corrected_delta = DecodePartData(after)
    require(original_delta.data == corrected_delta.data and original_frame.data != corrected_frame.data, "physical delta payload changed")
    return {
        "changed_fields": edits,
        "active_payload_sha256": {ORIGINAL_ATTACHMENT: digest(original_frame.data), CORRECTED_ATTACHMENT: digest(corrected_frame.data)},
        "delta_payload_sha256": digest(original_delta.data),
    }


def main():
    parser = ArgumentParser()
    parser.add_argument("previous", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    checkout = Path(__file__).resolve().parents[5]
    previous, output = (path.resolve() for path in (args.previous, args.output))
    require(all(not path.is_relative_to(checkout) for path in (previous, output)), "use external discovery directories")
    frozen_previous = (previous / "Freeze.json").read_bytes()
    frozen = loads(frozen_previous)
    require(frozen["schema"] == "kit.sw2026.rectangle-populated-attachment-discovery.v1" and frozen["heldout_acceptance"] is False,
            "the previous receipt must belong to the rectangle attachment discovery")
    path = PureWindowsPath(frozen["native_path"])
    require(path.is_absolute() and path.name == CASE_NAME, "the original encoded guest path is required")

    variants, request, observed = make_pair(path)
    corrected = variants["WithAttachment"]
    require(loads(dumps(observed["geometry"])) == frozen["geometry"] and observed["dimensions_m"] == frozen["dimensions_m"]
            and observed["variants"]["WithoutPartition"] == frozen["variants"]["WithoutPartition"], "the fresh neutral design changed")
    require(request == loads((previous / "NeutralRequest.json").read_bytes()), "neutral source request changed")
    original = (previous / "WithAttachment" / path.name).read_bytes()
    require(digest(original) == frozen["variants"]["WithAttachment"], "the frozen original attachment differs")
    before, after = (SldprtArchive.from_bytes(data).streams for data in (original, corrected))
    require(before.keys() == after.keys() and {name for name in before if before[name] != after[name]} == {KPartitionStream},
            "the edge intervention changed stream inventory or other logical streams")
    analysis = verify_anchors(before[KPartitionStream], after[KPartitionStream])
    data = {ORIGINAL_ATTACHMENT: original, CORRECTED_ATTACHMENT: corrected}
    receipt = {
        "schema": "kit.sw2026.rectangle-edge-anchor-discovery.v1", "native_path": str(path),
        "heldout_acceptance": False, "standalone_native_acceptance": "unmeasured",
        "previous_freeze_sha256": digest(frozen_previous), "construction_and_readback_file_opens": observed["construction_and_readback_file_opens"],
        "variants": {name: digest(blob) for name, blob in data.items()},
        "geometry": observed["geometry"], "dimensions_m": observed["dimensions_m"],
        "unchanged_logical_streams": {name: digest(before[name]) for name in sorted(before.keys() - {KPartitionStream})},
        "partition_stream_sha256": {ORIGINAL_ATTACHMENT: digest(before[KPartitionStream]), CORRECTED_ATTACHMENT: digest(after[KPartitionStream])},
        **analysis,
    }
    output.mkdir(parents=True, exist_ok=False)
    for name, blob in data.items():
        directory = output / name
        directory.mkdir()
        (directory / path.name).write_bytes(blob)
    (output / "AnchorFreeze.json").write_text(dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
