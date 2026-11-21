from dataclasses import dataclass

from convert.adapters.solidworks.Archive.Construction.Datums.Angles.AnglePlaneInput import AnglePlaneInput
from convert.adapters.solidworks.Archive.Construction.Datums.Angles.MakeAnglePlane import MakeAnglePlane
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


@dataclass(frozen=True, slots=True)
class AngularPlaneIntent:
    name: str
    angle_rad: float
    reverse: bool
    annotation_view: str
    design_intent: bool
    selected_leader: int
    shifted_point_m: tuple[float, float, float]


def typed_node(name, fields):
    return ArchiveNode(RuntimeClass(name, 1), fields)


def make_angular_plane_mut(system, settings, allocator, hinge, headers, intent):
    if type(intent) is not AngularPlaneIntent:
        raise ValueError("angular datum requires its own authored feature name and intent")
    input_value = AnglePlaneInput(
        intent.name, intent.angle_rad, intent.reverse, intent.annotation_view,
        intent.design_intent, intent.selected_leader, intent.shifted_point_m,
    )
    return MakeAnglePlane(system, settings, allocator, hinge, headers, input_value)
