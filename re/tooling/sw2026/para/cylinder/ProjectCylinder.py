from dataclasses import dataclass

from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import DatumTime
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import PartCandidate
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt, RequireNode, RequireRecord
from para.Partition import Partition, frame_payloads, write_payloads
from para.Tracking import signed_dword
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

    def stream(self):
        return frame_payloads(write_payloads(self.partition))


def project_cylinder(candidate, session, earlier_face_count=0):
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
    faces = tuple(
        Install(owner, "FACE_ID_2001", face_payload(role, feature_id, epoch, ordinal))
        for ordinal, (owner, role) in enumerate(topology.face_roles(marker), FIRST_PROCESS_FACE_ID + earlier_face_count)
    )
    installs = (
        *faces,
        Install(topology.body, "ATOM_ID_2001", (None, (atom_id,))),
        Install(topology.body, "LAST_BODY_MODIFYING_FEATURE_ID", (None, (feature_id,))),
    )
    active, pointers, next_id = register_attributes(partial, topology.body, installs, first_id)
    complete = tuple(augment(node, highest_node_id=next_id - 1) if node.kind == 12 else node for node in active)
    partition = collect_state(index_draft(complete, marks), pointers)
    side, = (node for node in complete if node.ref == topology.side)
    return CylinderProjection(partition, atom_id, side.fields["node_id"])
