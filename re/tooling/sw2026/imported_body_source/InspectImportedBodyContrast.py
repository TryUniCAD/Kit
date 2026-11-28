from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path

from LocalBodyEnvelope import LOCAL, PARTITION, ParaHeaderData, SldprtArchive, decode, encode
from ReplayImportedBaseBody import measure, require
from para.Partition import decode_active, frame_payloads, read_partition, write_payloads


SOURCE_REVISION = "9d003927b1800de099cdeeaf314f7aa42b3c0745"
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
ROLES = ("OtherShape", "RenamedFeature", "RenamedBody")


def digest(data):
    return sha256(data).hexdigest()


def compatibility_body_name(nodes):
    by_index = {node.index: node for node in nodes}
    definitions = {node.index for node in nodes if node.kind == 80
                   and by_index[node.fields["identifier"]].fields["string"] == "SDL/TYSA_NAME"}
    matches = [node for node in nodes if node.kind == 81 and node.fields["definition"] in definitions]
    if not matches:
        return None
    attribute, = matches
    body = by_index[attribute.fields["owner"]]
    value_index, = attribute.fields["fields"]
    value = by_index[value_index]
    require(body.kind == 12 and value.kind == 84, "expected the locally owned kernel compatibility name")
    return value.fields["values"]


def inspect_source(path, identity):
    source = path.read_bytes()
    require(digest(source) == identity["source_sha256"], "disclosed source bytes changed")
    archive = SldprtArchive.from_bytes(source)
    stream = archive.require(LOCAL)
    local = decode(stream)
    kernel = ParaHeaderData(local.kernel_stream)
    nodes = decode_active(local.kernel_stream[kernel.body_offset:])
    compatibility_name = compatibility_body_name(nodes)
    expected = identity["observed"]
    feature_name = expected["feature"]["name"]
    body_name = expected["body_name"]
    require(local.storage_key == feature_name, "native feature and local storage key differ")
    partition = archive.require(PARTITION)
    parsed = read_partition(partition)
    sole_node, = parsed.nodes
    require(sole_node.kind == 101 and sole_node.fields["body"] == 0, "the active configuration world has a body")
    require(encode(local) == stream and frame_payloads(write_payloads(parsed)) == partition,
            "local-body or partition bytes differ on typed re-emission")
    linked = measure(path, identity["source_sha256"])
    require(linked["feature_id"] == expected["feature"]["native_id"] and linked["feature_name"] == feature_name
            and linked["observed_suffix_text"] == ["", local.storage_key]
            and linked["observed_suffix_words"] == [1, 0], "the ordinary import suffix differs")
    explicit_name = linked["atom_body_name"]
    if explicit_name is None:
        require(compatibility_name is None and body_name == feature_name, "implicit body-name ownership differs")
    else:
        require(compatibility_name is not None and explicit_name == body_name, "explicit body-name ownership differs")
    require(digest(path.read_bytes()) == linked["source_sha256"], "disclosed native source changed during inspection")
    return {
        "file_sha256": linked["source_sha256"], "feature_id": linked["feature_id"], "feature_name": feature_name,
        "body_name": body_name, "atom_body_name": explicit_name, "kernel_compatibility_name": compatibility_name,
        "storage_key": local.storage_key,
        "suffix_text": linked["observed_suffix_text"], "suffix_words": linked["observed_suffix_words"],
        "linked_streams": linked["matched_streams"] | {
            LOCAL: {"bytes": len(stream), "sha256": digest(stream)},
            PARTITION: {"bytes": len(partition), "sha256": digest(partition)},
        },
        "raw_kernel": {"bytes": len(local.kernel_stream), "sha256": digest(local.kernel_stream), "nodes": len(nodes)},
        "native_geometry": {key: expected[key] for key in ("body_count", "topology", "mass_si")},
    }


def inspect(packet, expected_receipt):
    native_receipt = (packet / "Result.json").read_bytes()
    require(digest(native_receipt) == expected_receipt, "use the exact disclosed native contrast receipt")
    native = json.loads(native_receipt)
    require(native["passed"] and native["controls_healthy"] and native["distinct_processes"] == 8
            and native["source_revision"] == SOURCE_REVISION and native["oracle_sha256"] == ORACLE
            and native["oracle_version"] == "34.5.2.0604" and native["cohort"] == "contrast"
            and set(native["sources"]) == set(ROLES) and native["heldout_payloads_shared"] == 0,
            "the native source cohort is unqualified")
    require(digest((packet / "Job.json").read_bytes()) == native["job_sha256"], "the native contrast job changed")
    phases = native["phases"]
    require(tuple(phase["name"] for phase in phases) == (
        "ControlBefore", *(role + suffix for role in ROLES for suffix in ("Author", "Reopen")), "ControlAfter",
    ) and all(phase["passed"] for phase in phases), "the native authoring lifecycle is incomplete")
    require(len({(phase["process_id"], phase["process_creation_filetime"]) for phase in phases}) == 8,
            "the contrast phases do not have independent native process identities")
    read = {role: inspect_source(packet / (role + ".SLDPRT"), native["sources"][role]) for role in ROLES}
    plain, feature, body = (read[role] for role in ROLES)
    require(plain["storage_key"] != feature["storage_key"] == body["storage_key"]
            and feature["atom_body_name"] is None and body["atom_body_name"] == body["body_name"]
            and body["kernel_compatibility_name"] != body["atom_body_name"]
            and body["body_name"] != body["storage_key"], "the feature and body name controls failed to diverge")
    return {
        "schema": "kit.sw2026.imported-body-contrast.v1", "oracle_sha256": ORACLE,
        "oracle_file_version": native["oracle_version"], "native_receipt_sha256": expected_receipt,
        "author_revision": SOURCE_REVISION, "native_job_sha256": native["job_sha256"],
        "native_phases": [{key: phase[key] for key in ("name", "passed", "record_sha256")} for phase in phases],
        "native_distinct_processes": 8, "controls_healthy": True,
        "variants": read, "exact_linked_streams": sum(len(case["linked_streams"]) for case in read.values()),
        "native_writer_outputs": 0, "heldout_payloads_read": 0,
    }


if __name__ == "__main__":
    cli = ArgumentParser(description="Measure the disclosed native imported-body contrasts")
    cli.add_argument("packet", type=Path)
    cli.add_argument("--native-receipt-sha256", required=True)
    args = cli.parse_args()
    print(json.dumps(inspect(args.packet, args.native_receipt_sha256), indent=2, sort_keys=True))
