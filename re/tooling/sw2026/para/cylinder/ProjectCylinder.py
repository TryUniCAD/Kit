from dataclasses import dataclass

from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import DatumTime
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import PartCandidate
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt, ReadNodeName, RequireNode, RequireRecord
from para.DownstreamIds import install_part_downstream
from para.Partition import Partition, frame_payloads, write_payloads
from para.Tracking import body_match_tag, signed_dword, unchanged_face_stamp, unsigned
from para.cylinder.CylinderTopology import generated_cylinder
from para.rectangle.Allocate import allocate_marks, index_draft, positive_i32, require
from para.rectangle.AttributeChains import Install, register_attributes
from para.rectangle.RectangleAttributes import FIRST_PROCESS_FACE_ID, face_payload
from para.rectangle.RectanglePartition import augment, collect_state, complete_topology


@dataclass(frozen=True)
class CylinderProjection:
    partition: Partition
    reserved_body_atom_id: int
    lateral_face_node_id: int
    lateral_face_tag: int | None

    def stream(self):
        return frame_payloads(write_payloads(self.partition))


@dataclass(frozen=True)
class CylinderBodyTracking:
    body_tag: int
    body_stamp: int
    face_stamp: int | None = None


def tracking_installs(body, boss, tracking):
    tag = body_match_tag(positive_i32(tracking.body_tag, "body allocation tag"))
    stamp = signed_dword(unsigned(tracking.body_stamp, 32, "attached body stamp"))
    name = ReadNodeName(boss).encode("utf-16-le")
    name_words = tuple(int.from_bytes(name[index:index + 2], "little") for index in range(0, len(name), 2))
    return (
        Install(body, "BODY_MATCH", ((tag,),)),
        Install(body, "BODY_RECIPE_2001", (None, None)),
        Install(body, "ENT_TIME_STAMP_2001", (None, (stamp,))),
        Install(body, "SWIMPLICITBODYNAME_ID_U", (name_words, None)),
        Install(body, "BODY_IN_LIGHTWEIGHT_PERM", (None, (1,))),
    )


def face_tracking_installs(topology, faces, tracking):
    allocated = {
        member.ref: positive_i32(tracking.body_tag + offset, "generated kernel allocation")
        for offset, member in enumerate(topology[1:])
    }
    stamp = unsigned(tracking.face_stamp, 32, "tessellation update stamp")
    return allocated, tuple(
        Install(owner, "SWEntUnchanged", ((unchanged_face_stamp(allocated[owner], stamp),),))
        for owner, _ in faces
    )


def project_cylinder(candidate, session, earlier_face_count=0, *, tracking=None, downstream=None):
    require(type(candidate) is PartCandidate and candidate.CutValue is None,
            "the cylinder cache requires an actual generated ordinary part")
    require(type(earlier_face_count) is int and earlier_face_count >= 0,
            "the current session requires its actual earlier face-allocation count")
    part = RequireNode(candidate.SystemValue.RootValue, "moPart_c")
    boss = RequireNode(candidate.BossValue.FeatureValue, "moExtrusion_c")
    manager = RequireRecord(part.FieldsValue["fd88"])
    require(not manager["atoms"] and manager["n6c"] == 0 and manager["fa8"] == 0
            and not any(boss.FieldsValue[k] for k in ("has_f528", "has_f530", "n494"))
            and not any("Partition" in name for name in candidate.StreamsValue),
            "attribute projection requires the fresh actual manager and feature output")
    feature_id = positive_i32(FieldInt(boss.FieldsValue, "f08"), "owning extrusion")
    epoch = signed_dword(DatumTime(candidate.HeaderValue, feature_id))
    marks = allocate_marks(session)
    topology = generated_cylinder(candidate, marks)
    marker = FieldInt(candidate.ProfileValue.GeometryValue.ArcValue.FieldsValue, "f08")
    atom_id = positive_i32(FieldInt(manager, "f260") + 1, "next body atom in the part")
    partial, first_id = complete_topology(topology.nodes)
    side, start, end = topology.face_roles(marker)
    faces = tuple(
        Install(owner, "FACE_ID_2001", face_payload(role, feature_id, epoch, ordinal))
        for ordinal, (owner, role) in enumerate((start, end, side), FIRST_PROCESS_FACE_ID + earlier_face_count)
    )
    tag = None
    tracking_rows = ()
    if tracking is not None:
        tracking_rows = tracking_installs(topology.body, boss, tracking)
        if tracking.face_stamp is not None:
            assigned, face_tracking = face_tracking_installs(partial, (start, end, side), tracking)
            tag = assigned[topology.side]
            tracking_rows += face_tracking
    installs = (
        *faces,
        *tracking_rows,
        Install(topology.body, "ATOM_ID_2001", (None, (atom_id,))),
        Install(topology.body, "LAST_BODY_MODIFYING_FEATURE_ID", (None, (feature_id,))),
    )
    if downstream is not None:
        installs = install_part_downstream(partial, installs, downstream)
    active, pointers, next_id = register_attributes(partial, topology.body, installs, first_id)
    complete = tuple(augment(node, highest_node_id=next_id - 1) if node.kind == 12 else node for node in active)
    partition = collect_state(index_draft(complete, marks), pointers)
    lateral, = (node for node in complete if node.ref == topology.side)
    return CylinderProjection(partition, atom_id, lateral.fields["node_id"], tag)
