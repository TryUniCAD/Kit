from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path

from LocalBodyEnvelope import LOCAL, PARTITION, decode, encode
from LocalBodyKernel import BODY, EDGE, FACE, VERTEX, _render_local, audit_nodes, decode_local, fingerprint
from ReplayImportedBaseBody import SOURCE, measure, require
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from para.Partition import frame_payloads, read_partition, write_payloads


ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
JOB = "313d1f9b962beda3ef0e4d1617b5b9d935896db4a0700ce65f224c87d96162cd"
RECEIPT = "bbaa59c9661882912fdc0f140feb864824a9ddc36609e902e359d8c50ffd1105"
CYLINDERS = {
    "CylinderZ": "ef72c75f230331903726a4e48ca61682736289dba78261d654071f2fe2a54166",
    "CylinderReverseY": "91a3a675d932d0f14c886446885980d484beb66a4f821d5ecfe9908e41182179",
}


def attribute_values(nodes):
    indexed = {node.index: node for node in nodes}
    by_owner = {}
    for node in nodes:
        if node.kind != 81:
            continue
        fields = node.fields
        definition = indexed[fields["definition"]]
        name = indexed[definition.fields["identifier"]].fields["string"]
        values = tuple(indexed[index].fields["values"] if index else None for index in fields["fields"])
        by_owner.setdefault(fields["owner"], {})[name] = values
    return by_owner


def observe(path, expected_sha256, expected_geometry):
    raw = path.read_bytes()
    require(sha256(raw).hexdigest() == expected_sha256, "disclosed topology source hash differs")
    archive = SldprtArchive.from_bytes(raw)
    replay = measure(path, expected_sha256)
    require(len(replay["matched_streams"]) == 5, "shared replay did not cover all five archive streams")
    framed = archive.require(LOCAL)
    local = decode(framed)
    require(encode(local) == framed, "local envelope changed on typed re-emission")
    nodes, header_size = decode_local(local.kernel_stream)
    geometry = tuple(sum(node.kind == kind for node in nodes) for kind in (VERTEX, EDGE, FACE))
    require(geometry == expected_geometry and _render_local(nodes) == local.kernel_stream,
            "local transmit topology or bytes disagree")
    require(nodes[0].kind == BODY, "local geometry needs a single primary body")
    graph = audit_nodes(nodes)

    partition_data = archive.require(PARTITION)
    partition = read_partition(partition_data)
    world, = partition.nodes
    require(world.kind == 101 and world.fields["body"] == 0 and
            frame_payloads(write_payloads(partition)) == partition_data, "active empty partition disagrees")
    link = ReadNativeLink(archive, 0)
    manager = link.ConfigValue.RootValue.FieldsValue["fd88"]
    feature, = (row for row in link.ResolvedValue.RootsValue if row.ClassValue.NameValue == "moBaseBody_c")
    fields = feature.FieldsValue
    atom, = (row["o"] for row in fields["f528"]["items"])
    managed_atom, = (row["o"] for row in manager["atoms"])
    atom_id, = (row["v"] for row in fields["f498"])
    body = attribute_values(nodes)[nodes[0].index]
    partition_mark = fields["f3d0"].FieldsValue["f18"]
    tracked_id, = body["ATOM_ID_2001"][1]
    tracked_feature, = body["LAST_BODY_MODIFYING_FEATURE_ID"][1]
    body_tag = atom.FieldsValue["f180"]
    match_values = body["BODY_MATCH"][0] if "BODY_MATCH" in body else None
    body_stamp, = body["ENT_TIME_STAMP_2001"][1]
    require(atom is managed_atom and manager["n6c"] == 1 and atom.ClassValue.NameValue == "moAtom_c"
            and atom_id == tracked_id == atom.FieldsValue["f140"]
            and fields["f08"] == tracked_feature == atom.FieldsValue["f12c"] == atom.FieldsValue["f130"]
            and body_tag == atom.FieldsValue["f1b0"] and match_values in (None, (body_tag,))
            and local.storage_key == fields["local_storage_key"] == replay["feature_name"]
            and partition_mark == world.fields["current_id"] == partition.history[0].mark.fields["id"],
            "local payload, native feature, managed atom and active partition disagree")
    header = ReadHeaderGraph(archive.require("Header2"), 19000)
    return {
        "source": fingerprint(raw), "shared_archive": replay["matched_streams"],
        "map_base": replay["resolved_base"], "map_final": replay["resolved_map"],
        "local_envelope": fingerprint(framed), "empty_active_partition": fingerprint(partition_data),
        "local_transmit": {**fingerprint(local.kernel_stream), "header_bytes": header_size,
                           "nodes": graph["node_kinds"], "resident_nodes": graph["resident_nodes"],
                           "attribute_count": graph["attributes"]["attribute_count"],
                           "nonresident_pointers": graph["nonresident_pointer_counts"]},
        "storage_key": local.storage_key, "topology": dict(zip(("vertices", "edges", "faces"), geometry, strict=True)),
        "owner_links": {"feature_id": tracked_feature, "atom_id": tracked_id, "archive_body_tag": body_tag,
                        "local_body_match_attribute": match_values,
                        "display_mode": atom.FieldsValue["f19c"], "partition_mark": partition_mark,
                        "body_stamp": body_stamp, "saved_header_stamp": header.FieldsValue["f44"]},
    }


def evaluate(folder, box):
    job = (folder / "Job.json").read_bytes()
    raw_receipt = (folder / "Result.json").read_bytes()
    native = json.loads(raw_receipt)
    phases = native["phases"]
    phase_names = ("ControlBefore", *(name + phase for name in CYLINDERS for phase in ("Author", "Reopen")), "ControlAfter")
    require(sha256(job).hexdigest() == native["job_sha256"] == JOB and sha256(raw_receipt).hexdigest() == RECEIPT
            and native["oracle_version"] == "34.5.2.0604" and native["oracle_sha256"] == ORACLE
            and tuple(row["name"] for row in phases) == phase_names and all(row["passed"] for row in phases)
            and len({(row["process_id"], row["process_creation_filetime"]) for row in phases}) == len(phases)
            and native["passed"] and native["controls_healthy"] and not native["writer_outputs"],
            "native topology source protocol or controls disagree")
    observations = {"BoxReference": observe(box, SOURCE, (8, 12, 6))}
    for name, digest in CYLINDERS.items():
        evidence = native["sources"][name]
        require(evidence["source_sha256"] == digest, "cylinder source hash differs from native evidence")
        measured = evidence["observed"]
        topology = measured["topology"]
        require(measured["body_count"] == 1 and measured["feature"]["type"] == "BaseBody" and
                topology == {"vertices": 0, "edges": 2, "faces": 3, "planar_faces": 2, "cylindrical_faces": 1},
                "native topology measurements disagree")
        observations[name] = observe(folder / f"{name}.SLDPRT", digest, (0, 2, 3))
        observations[name]["native_observation"] = measured
    require({row["owner_links"]["display_mode"] for row in observations.values()} == {6} and
            set(row["owner_links"]["archive_body_tag"] for row in observations.values()) == {316, 536} and
            observations["BoxReference"]["owner_links"]["local_body_match_attribute"] is None and
            all(observations[name]["owner_links"]["local_body_match_attribute"] == (316,) for name in CYLINDERS),
            "topology contrast does not separate display mode from linkage tags")
    return {"schema": "kit.sw2026.imported-body-topology.v1", "oracle_version": native["oracle_version"],
            "oracle_sha256": ORACLE, "native_job_sha256": JOB, "native_receipt_sha256": RECEIPT,
            "author_revision": native["source_revision"], "native_processes": len(phases),
            "controls_healthy": True, "native_phases": [{"name": row["name"], "record_sha256": row["record_sha256"]} for row in phases],
            "observations": observations, "exact_replays_per_source": 7, "heldout_payloads_read": 0,
            "native_writer_outputs": 0, "native_writer_acceptance": False}


if __name__ == "__main__":
    parser = ArgumentParser(description="Measure the disclosed native imported topology contrast")
    parser.add_argument("cylinder_batch", type=Path)
    parser.add_argument("box_reference", type=Path)
    args = parser.parse_args()
    print(json.dumps(evaluate(args.cylinder_batch, args.box_reference), indent=2, sort_keys=True, allow_nan=False))
