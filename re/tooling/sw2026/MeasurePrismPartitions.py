from collections import Counter

from AuditKeywordCorpus import digest, require
from convert.Geometry.Parasolid import DecodePartData, EncodePartData, ParaHeaderData
from convert.adapters.solidworks.Archive.Partition.CheckXmtGraph import CheckXmtGraph
from convert.adapters.solidworks.Archive.Partition.ReadActiveNodes import ReadActiveNodes
from convert.adapters.solidworks.Archive.Partition.ReadHistMarks import ReadHistMarks
from convert.adapters.solidworks.Archive.Partition.Sweeps.EncodeSweepXmt import EncodeSwNodes
from convert.adapters.solidworks.Container.Format import KGhostPartition, KPartitionStream
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.BindSwGhosts import GhostBodyId
from para.CompareRectangle import archive_binding, inspect_binding, ownership
from para.Partition import description, frame_payloads, read_partition, write_payloads


def measure_payload(frame):
    header = ParaHeaderData(frame.data)
    require(header is not None and header.description.encode("ascii") == description("partition"),
            "unexpected active or ghost frame description")
    nodes = ReadActiveNodes(frame.data)
    CheckXmtGraph(nodes)
    rebuilt = EncodeSwNodes(tuple(nodes.values()), description("partition"))
    require(rebuilt == frame.data, "typed SDK node replay differs")
    return nodes, rebuilt


def origin_ghost_binding(archive, nodes):
    world = nodes[1]
    body = nodes[world.Integer("body")]
    shell = nodes[body.Integer("shell")]
    vertex = nodes[shell.Integer("vertex")]
    point = nodes[vertex.Integer("point")]
    require(body.KindValue == 12 and body.Integer("owner") == world.IndexValue
            and body.Integer("body_type") == 2 and body.Integer("edge") == 0
            and shell.Integer("edge") == shell.Integer("face") == 0
            and body.Integer("vertex") == vertex.IndexValue
            and vertex.Integer("owner") == shell.IndexValue and point.Integer("owner") == vertex.IndexValue
            and point.FieldsValue["pvec"] == (0.0, 0.0, 0.0),
            "ghost is outside the ordinary owned origin-point wire profile")
    body_id = GhostBodyId(nodes, body)
    manager = ReadNativeLink(archive, 0).ConfigValue.RootValue.FieldsValue["fd90"]
    row, = manager["objects"]
    record = row["o"]
    require(manager["n"] == 1 and manager["fe0"] == 2 and manager["f80"] == body_id == record["f08"]
            and record["f0c"] == 20 and record["nb0"] == 1 and record["fa0"] == [{"v": -1}],
            "ghost body does not join to its type-20 linked configuration owner")
    return {"body_attribute_id": body_id, "manager_row_type": record["f0c"],
            "usage_marker": record["fa0"][0]["v"], "point_model_m": point.FieldsValue["pvec"]}


def measure_prism_partitions(archive):
    main = archive.require(KPartitionStream)
    ghost = archive.require(KGhostPartition)
    active, delta = DecodePartData(main)
    ghost_frame, = DecodePartData(ghost)
    nodes, original_rebuilt = measure_payload(active)
    ghost_nodes, ghost_rebuilt = measure_payload(ghost_frame)
    require(EncodePartData(ghost_rebuilt) == ghost, "ghost member compression differs")
    marks = ReadHistMarks(delta.data, nodes)
    partition = read_partition(main)
    payloads = write_payloads(partition)
    require(payloads == (original_rebuilt, delta.data) and frame_payloads(payloads) == main,
            "typed active or rollback partition replay differs")
    owners = ownership(partition)
    binding = archive_binding(archive)
    inspect_binding(partition, owners, binding)
    require(marks == (binding["feature_mark"], binding["model_activation_mark"]),
            "SDK mark anchors disagree with the owning native graph")
    return {
        KPartitionStream: {
            "bytes": len(main), "sha256": digest(main), "active_nodes": len(nodes),
            "active_sha256": digest(active.data), "rollback_sha256": digest(delta.data),
            "selected_and_activation_marks": marks, "feature_id": binding["feature_id"],
            "body_atom_id": owners["atom_id"],
        },
        KGhostPartition: {
            "bytes": len(ghost), "sha256": digest(ghost),
            "node_kinds": dict(Counter(node.KindValue for node in ghost_nodes.values())),
            "binding": origin_ghost_binding(archive, ghost_nodes),
        },
    }
