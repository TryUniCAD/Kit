from argparse import ArgumentParser
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from json import dumps
from sys import addaudithook
from uuid import NAMESPACE_URL, uuid5

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Container.Format import KPartitionStream
from downstream.Body import COLLECTIONS, ROOT
from downstream.CheckCollectedSurfaceClones import surface_owner
from downstream.CheckSurfaceIdentities import authored_cylinder
from downstream.CollectorProjection import fresh_cylinder_collector_fields
from downstream.Components import read_component_body, write_component_body
from downstream.Storage import ConfigurationCache, cache_path, store_part_caches
from drawing_edges.CheckDownstreamPartition import inspect_attributes, number_words
from para.DownstreamIds import EDGE_DEFINITION, FACE_DEFINITION, allocate_fresh_downstream, owned_solid_chains, owner_key
from para.Partition import read_partition
from para.Tracking import FILETIME_TICKS_PER_SECOND
from para.concentric.CylinderFace import make_feature_file, words
from para.cylinder.CylinderAttachment import attach_cylinder_mut
from para.cylinder.CylinderTopology import generated_cylinder
from para.rectangle.Allocate import allocate_marks
from para.rectangle.RectanglePartition import complete_topology


def collector_body(fields):
    empty = {field.NameValue: [] for field in COLLECTIONS}
    return ArchiveNode(ROOT, empty | fields)


def attached_with_partition(attachment, partition):
    return replace(attachment, projection=replace(attachment.projection, partition=partition))


def negative_cases(attachment, allocation):
    partition = attachment.projection.partition
    edge_name, = (node.index for node in partition.nodes if node.fields.get("string") == EDGE_DEFINITION)
    modified = tuple(
        replace(node, fields=node.fields | {"string": "EDGE_PERM_ID_2001"}) if node.index == edge_name else node
        for node in partition.nodes
    )
    foreign_owner = uuid5(allocation.owner, "different file")
    return (
        (attachment, replace(allocation, next_id=allocation.next_id + 1)),
        (attachment, replace(allocation, updated=allocation.updated - FILETIME_TICKS_PER_SECOND)),
        (attachment, replace(allocation, owner=foreign_owner, key=owner_key(foreign_owner))),
        (attached_with_partition(attachment, replace(partition, nodes=modified)), allocation),
    )


def main():
    cli = ArgumentParser()
    cli.add_argument("variant", type=int, choices=(1, 2))
    spec = cli.parse_args()
    for encoding in ("utf-8", "utf-16le", "utf-16be", "cp1252", "latin-1"):
        lookup(encoding)
    for validator in ("DocumentAssemblyValidate", "DocumentFeatureValidate", "DocumentReferenceValidate"):
        import_module("interchange.document.Validation." + validator)
    attempts = []
    active = True

    def guard(event, arguments):
        if active and event in {"open", "subprocess.Popen", "os.system", "os.posix_spawn", "socket.connect"}:
            attempts.append(event)
            raise RuntimeError("unexpected runtime operation: " + event)

    addaudithook(guard)
    try:
        candidate, session, events, target = authored_cylinder(spec.variant)
        owner = uuid5(NAMESPACE_URL, "urn:kit:solidworks:downstream:" + target)
        draft = generated_cylinder(candidate, allocate_marks(session))
        topology, _ = complete_topology(draft.nodes)
        faces, edges = owned_solid_chains(topology)
        allocation = allocate_fresh_downstream(faces, edges, owner, session.update_second,
                                                session.update_fraction, is_assembly=False)
        attachment = attach_cylinder_mut(candidate, session, events, 11 * spec.variant, downstream=allocation)
        feature_file = make_feature_file(attachment.candidate)
        fields = fresh_cylinder_collector_fields(attachment, allocation, feature_file)
        partition = read_partition(attachment.streams[KPartitionStream])
        assert partition == attachment.projection.partition
        reversed_table = replace(partition, nodes=tuple(reversed(partition.nodes)))
        from_reversed = fresh_cylinder_collector_fields(
            attached_with_partition(attachment, reversed_table), allocation, feature_file,
        )

        body = collector_body(fields)
        raw = write_component_body(body)[0]
        assert write_component_body(collector_body(from_reversed))[0] == raw
        config_id = attachment.candidate.CurrentConfig.FieldsValue["f08"]
        state = ConfigurationCache(config_id, True, False, True, body, False)
        streams = store_part_caches(attachment.streams, (state,))
        container = BuildSldprt(streams, FormatVersion=4)
        record = SldprtArchive.from_bytes(container)
        assert record.streams == streams and record.require(cache_path(config_id)) == raw
        assert all(record.require(name) == data for name, data in attachment.streams.items())
        decoded, maps = read_component_body(record.require(cache_path(config_id)))
        written = decoded.FieldsValue
        assert written["f30"] == str(owner)
        assert (written["f38_high"], written["f38_low"]) == number_words(str(owner))
        assert written["f08"] == len(faces) + len(edges) + 1
        assert written["f28"] == session.update_second
        assert write_component_body(decoded)[0] == raw

        nodes = {node.index: node for node in partition.nodes}
        emitted_by_id = {node.fields["node_id"]: node for node in partition.nodes if node.kind == 14}
        attributes = inspect_attributes(partition)
        expected = sorted(
            (attributes[(FACE_DEFINITION, number)][0], words(nodes, node, "FACE_ID_2001", 2))
            for number, node in emitted_by_id.items()
        )
        found = []
        owners = []
        for member in written["f40"]:
            rep = member["object"]
            local = rep.FieldsValue
            owners.append(surface_owner(rep))
            feature = local["f10"]["f10"].FieldsValue["f10"]
            if rep.ClassValue.NameValue == "moEndFaceSurfIdRep_c":
                found.append((40, feature["f00"], feature["f08"], 0, local["f38"], local["f3c"]))
            else:
                assert rep.ClassValue.NameValue == "moFromSktEntSurfIdRep_c"
                found.append((74, feature["f00"], feature["f08"], 0, local["f38"]))
        assert found == [key for _, key in expected]
        assert len({id(owner) for owner in owners}) == len(faces)
        assert all(owner.FieldsValue["f78"] == -1 for owner in owners)
        assert len([k for k in attributes if k[0] == EDGE_DEFINITION]) == len(edges)

        refused = 0
        for proposed, proposed_allocation in negative_cases(attachment, allocation):
            try:
                fresh_cylinder_collector_fields(proposed, proposed_allocation, feature_file)
            except ValueError:
                refused += 1
            else:
                raise AssertionError("collector accepted a foreign body, owner, time or allocation")
    finally:
        active = False
    print(dumps({
        "passed": True, "variant": spec.variant, "counts": {"collected": len(found), "face": len(faces), "edge": len(edges)},
        "next_downstream_id": written["f08"], "mapped_roles": found, "owner": written["f30"],
        "owner_hash": (written["f38_high"], written["f38_low"]), "cache_bytes": len(raw),
        "cache_sha256": sha256(raw).hexdigest(), "container_sha256": sha256(container).hexdigest(),
        "preserved_part_streams": len(attachment.streams), "map_counter": maps.CounterValue,
        "invalid_inputs_refused": refused, "runtime_io_attempts": len(attempts), "native_runs": 0,
        "scope": "generated ordinary collector prefix and members in a typed cache-body witness",
    }, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
