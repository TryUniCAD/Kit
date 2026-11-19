from dataclasses import dataclass

from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Config.ConfigGraph import ConfigGraph
from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import DatumTime
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Container.Format import KPartitionStream
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismMgr import CheckPrismMgr
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismLoop import ReadPrismLoop
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from downstream.CacheInputs import ARCHIVE_VERSION, finalized_part_prefix, topology_node
from downstream.Components import make_local_unit_component
from downstream.FaceOperands import single_loop_face_operands
from interchange.Features.FeatureExtrude import ExtrudeEnd
from para.Partition import read_partition
from para.Tracking import signed_dword
from para.concentric.CylinderFace import make_feature_file, node, words


@dataclass(frozen=True)
class PrismFaceOwners:
    SystemValue: ConfigGraph
    CurrentConfig: ArchiveNode
    atom_id: int
    feature_id: int
    creation: int
    markers: frozenset[int]

    @property
    def HeaderValue(self):
        return self.SystemValue.HeaderValue


def read_prism_face_owners(archive, partition):
    link = ReadNativeLink(archive, 0)
    config_graph = link.ConfigValue
    model = config_graph.RootValue
    header = config_graph.HeaderValue
    manager = ReadCmgrMut(archive.require("Contents/CMgr"), ARCHIVE_VERSION)
    CheckPrismMgr(manager)
    config = manager.RootValue.FieldsValue["f360"]
    if (model.ClassValue.NameValue != "moPart_c" or model.FieldsValue["f1010"] != 1
            or config.FieldsValue["f860"] != header.FieldsValue["f40"]):
        raise ValueError("prism face constructors need the actual active body and configuration header")
    config.FieldsValue["owner"] = model

    feature_roots = {NativeNodeId(root): root for root in link.ResolvedValue.RootsValue if root is not None}
    boss, = (root for root in feature_roots.values() if root.ClassValue.NameValue == "moExtrusion_c")
    extrude = ReadExtrude(link, boss, feature_roots)
    if extrude.ModeValue != ExtrudeEnd.KBlind or extrude.IsReversed:
        raise ValueError("prism face constructors require a forward blind boss")
    loop = ReadPrismLoop(extrude.ProfileValue, link)
    marker_ids = frozenset(line.PermanentId for line in loop.LinesValue)
    if len(marker_ids) != 4:
        raise ValueError("four native sketch lines must have unique permanent IDs")

    body, = (body for body in partition.nodes if body.kind == 12)
    nodes = {item.index: item for item in partition.nodes}
    atom_id, = words(nodes, body, "ATOM_ID_2001", 1)
    producer, = words(nodes, body, "LAST_BODY_MODIFYING_FEATURE_ID", 1)
    match, = words(nodes, body, "BODY_MATCH", 0)
    atom, = (row["o"] for row in model.FieldsValue["fd88"]["atoms"])
    atom_fields = atom.FieldsValue
    feature_id = NativeNodeId(boss)
    if (atom.ClassValue.NameValue != "moAtom_c" or atom_fields["f140"] != atom_id or atom_id <= 0
            or atom_fields["f12c"] != feature_id or atom_fields["f130"] != feature_id
            or atom_fields["f180"] != match or producer != feature_id):
        raise ValueError("partition, atom manager and extrusion must name the same generated body")
    return PrismFaceOwners(config_graph, config, atom_id, feature_id, DatumTime(header, feature_id), marker_ids)


def prism_surface_keys(partition, operands, owners):
    nodes = {item.index: item for item in partition.nodes}
    key_by_face = {}
    for operand in operands:
        face = operand.face
        carrier = topology_node(nodes, face.fields["surface"], 50)
        if carrier.fields["owner"] != face.index:
            raise ValueError("prism face reference requires its actual owned planar carrier")
        code, producer, creation, flags, marker, *extra = words(nodes, face, "FACE_ID_2001", 2)
        if (producer, creation, flags) != (owners.feature_id, signed_dword(owners.creation), 0):
            raise ValueError("native primary surface identity belongs to a different feature or epoch")
        if (code == 40 and marker in (0, 1) and extra == [0]) or (
            code == 74 and marker in owners.markers and not extra
        ):
            key_by_face[face.index] = (code, marker)
        else:
            raise ValueError("unsupported primary ID for an ordinary prism surface")
    expected = {(40, 0), (40, 1)} | {(74, marker) for marker in owners.markers}
    if len(key_by_face) != len(expected) or set(key_by_face.values()) != expected:
        raise ValueError("ordinary prism needs the actual two caps and four distinct profile sides")
    return key_by_face


def make_surface_representation(key, owners, file):
    kind, marker = key
    keeper = node("moFR_c", {"f08": file, "f10": {"f00": owners.feature_id, "f08": owners.creation}})
    fields = {"f10": {"f08": None, "f10": keeper}, "f38": marker}
    if kind == 40:
        return node("moEndFaceSurfIdRep_c", fields | {"f3c": 0})
    return node("moFromSktEntSurfIdRep_c", fields)


def make_prism_face_constructor(operand, keys, owners, feature_file):
    inline_keys = tuple(keys[face.index] for face in operand.inline_faces[:-1])
    if (len(inline_keys) != 5 or len(set(inline_keys)) != 5 or operand.inline_faces[0] is not operand.face
            or operand.inline_faces[-1] is not None):
        raise ValueError("the ordinary face constructor needs one independent selected four-fin loop")
    inline_ids = [
        {"f08": make_surface_representation(key, owners, feature_file)} for key in inline_keys
    ] + [{"f08": None}]
    data = {
        "f10": [{"key": slot, "value": number} for slot, number in operand.initial_role_values],
        "f20": [], "f38": 0, "f40_0": 0, "f40_1": 0,
    }
    face = node("moFaceRef_c", {
        "f60": 1, "f64": 0, "f08": len(inline_ids), "fe8": 0, "f70": 0,
        "f28": 1e100, "f30": 1e100, "f40": None, "f10": inline_ids,
        "f48": 0, "nd0": 0, "fd0": [], "fec": ARCHIVE_VERSION,
        "has_f18": 1, "f18": data, "nf0": 0, "ff0": [],
    })
    fields = dict.fromkeys(
        ("f68", "f20", "f30", "f70", "f84", "fa0", "f34", "f48",
         "has_fb0", "has_fb8", "has_fc0", "has_fc8", "has_fd0", "alias_present"), 0,
    )
    fields.update(dict.fromkeys(("f90", "f94", "f98", "f9c"), -1))
    fields.update(f58=make_local_unit_component(owners), f18=owners.atom_id, f1c=owners.atom_id,
                  f4c=ARCHIVE_VERSION, fe8=face, ff0=None)
    return {"object": node("moCompFace_c", fields), "word": operand.downstream_id}


def prism_face_constructor_fields(archive, allocation, *, special_id_map_present):
    partition = read_partition(archive.require(KPartitionStream))
    owners = read_prism_face_owners(archive, partition)
    operands = single_loop_face_operands(
        partition, allocation, owners.HeaderValue.FieldsValue["f48"],
        special_id_map_present=special_id_map_present,
    )
    keys = prism_surface_keys(partition, operands, owners)
    feature_file = make_feature_file(owners)
    constructed = [make_prism_face_constructor(row, keys, owners, feature_file) for row in operands]
    name, high, low = allocation.archive_owner_fields
    return finalized_part_prefix(owners, allocation.next_id) | {
        "f30": name, "f38_high": high, "f38_low": low, "f48": constructed,
    }
