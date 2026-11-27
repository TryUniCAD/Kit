from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path

from convert.Geometry.Parasolid import (
    ParaHeaderData,
    ParseVertexUse,
    RecordStart,
    RefsValue,
)
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Parasolid import DecodePartition

SOURCE_SHA = "dcea552fa4751563c124fb1dc571f3e0b36c0ce37ce39610b45f7717d8687115"
ACTIVE_SHA = "af3dd2ac0b09608ef1d48207b0cce8d0a395fdc4adabd97a53522e12c4c9cf56"
OWNER_AUTHORITY = "e20e859e81c8f71f34629e6ed6aa97affca47bae1a77afaffcf81c71edf847f3"


def digest(raw):
    return sha256(raw).hexdigest()


def demand(condition, message):
    if not condition:
        raise ValueError(message)


def require_node(nodes, index, kind):
    row = nodes[index]
    demand(row["kind"] == kind, f"index {index} is not kind {kind}")
    return row


def read_active(source):
    archive = SldprtArchive.from_bytes(source)
    (active,) = (
        row
        for row in DecodePartition(archive.Require("Contents/Config-0-Partition"))
        if row.kind == "partition"
    )
    demand(digest(active.data) == ACTIVE_SHA, "unexpected normalized active payload")
    header = ParaHeaderData(active.data)
    demand(header is not None, "active payload has no header")
    return active.data[header.body_offset :]


def check_vertex(row, nodes, body):
    index = row["index"]
    fields = row["fields"]
    demand(fields["owner"] == 2, "record is outside the examined body")
    point = require_node(nodes, fields["point"], 29)
    demand(point["fields"]["owner"] == index, "nonreciprocal point owner")
    start, end = row["body_span"]
    demand(digest(body[start:end]) == row["wire_sha256"], "vertex span digest differs")
    record_offset = RecordStart(body, start, 18)
    demand(record_offset is not None, "legacy recognizer cannot read kind18 header")
    legacy_refs = RefsValue(body, record_offset + 6, 5)
    names = ("attributes_features", "halfedge", "previous", "next", "point")
    demand(
        legacy_refs == tuple(fields[name] + 1 for name in names),
        "reference domains differ",
    )
    head = fields["attributes_features"]
    accepted = ParseVertexUse(body, start) is not None
    demand(accepted == (head == 0), "unexpected legacy admission at saved bytes")
    attribute = None
    if head:
        saved = require_node(nodes, head, 81)["fields"]
        demand(saved["owner"] == index, "nonreciprocal attribute owner")
        definition = require_node(nodes, saved["definition"], 80)["fields"]
        identifier = require_node(nodes, definition["identifier"], 79)["fields"][
            "string"
        ]
        demand(
            identifier == "VERTEX_AUTOMATION_2_2001",
            "unexpected saved attribute definition",
        )
        attribute = {
            "index": head,
            "fields": saved,
            "definition_index": saved["definition"],
            "definition_identifier": identifier,
        }
    return {
        "index": index,
        "scanner_attribute": index + 1,
        "span": [start, end],
        "point_index": point["index"],
        "point_m": point["fields"]["pvec"],
        "attributes": attribute,
        "legacy_first_reference": legacy_refs[0],
        "legacy_admitted_saved_bytes": accepted,
    }


def check_type_chain(nodes, attributes):
    selected = {row["index"] for row in attributes}
    (first,) = (
        row["index"] for row in attributes if row["fields"]["previous_of_type"] == 0
    )
    chain = []
    previous = 0
    while first:
        demand(
            first in selected and first not in chain,
            "attribute type chain is open or cyclic",
        )
        fields = require_node(nodes, first, 81)["fields"]
        demand(
            fields["previous_of_type"] == previous,
            "nonreciprocal previous-of-type link",
        )
        chain.append(first)
        previous, first = first, fields["next_of_type"]
    demand(set(chain) == selected, "attribute type chain is incomplete")
    return chain


def main(source, walk_path, output):
    if output.exists():
        raise FileExistsError(output)
    raw = source.read_bytes()
    walk_raw = walk_path.read_bytes()
    demand(digest(raw) == SOURCE_SHA, "unexpected native saved derivative")
    walk = json.loads(walk_raw)
    demand(
        walk["source_sha256"] == SOURCE_SHA
        and walk["active_payload_sha256"] == ACTIVE_SHA,
        "walk addresses another active payload",
    )
    demand(
        walk["physical_complete"]
        and walk["all_declared_pointer_targets_exist"]
        and not walk["unknown_records_skipped"],
        "walk is partial",
    )
    demand(
        walk["authorities"]["141"]["sha256"] == OWNER_AUTHORITY,
        "owner descriptor is unqualified",
    )
    body = read_active(raw)
    nodes = {row["index"]: row for row in walk["records"]}
    demand(
        len(nodes) == len(walk["records"]) == 189, "unexpected complete typed inventory"
    )
    vertex_rows = [
        check_vertex(row, nodes, body) for row in nodes.values() if row["kind"] == 18
    ]
    demand(len(vertex_rows) == 8, "unexpected number of typed vertices")
    rejected = [row for row in vertex_rows if not row["legacy_admitted_saved_bytes"]]
    demand(
        {row["scanner_attribute"] for row in rejected} == {69, 73, 78},
        "legacy omission set differs",
    )
    chain = check_type_chain(nodes, [row["attributes"] for row in rejected])
    demand(
        source.read_bytes() == raw and walk_path.read_bytes() == walk_raw,
        "input bytes changed",
    )
    receipt = {
        "schema": "kit.research.p03-vertex-attribute-owners.v1",
        "source_sha256": SOURCE_SHA,
        "active_sha256": ACTIVE_SHA,
        "walk_sha256": digest(walk_raw),
        "method_sha256": digest(Path(__file__).read_bytes()),
        "vertex_rows": vertex_rows,
        "attribute_type_chain": chain,
        "payload_fields_written": 0,
        "unknown_records_skipped": 0,
        "native_launches": 0,
        "public_decoder_calls": 0,
    }
    with output.open("x", encoding="utf-8", newline="\n") as target:
        json.dump(receipt, target, indent=2, sort_keys=True)
        target.write("\n")


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--walk", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    main(arguments.source, arguments.walk, arguments.output)
