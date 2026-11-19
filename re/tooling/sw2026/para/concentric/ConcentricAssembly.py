from dataclasses import dataclass, replace
from io import BytesIO

from ConcentricNeutralAdmission import bind_cylinder, project_concentric
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Archive.Construction.Assembly.EmitAsmStreams import EmitAsmStreams
from convert.adapters.solidworks.Archive.Construction.Assembly.Headers.MakeAsmHeaders import MakeAsmHeaders
from convert.adapters.solidworks.Archive.Construction.Assembly.MakeAsmBase import MakeAsmBase
from convert.adapters.solidworks.Archive.Construction.Assembly.Occurrences.PutPartRefsMut import PutPartRefsMut
from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import PrincipalFrame
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Container.Container import BuildSldprt
from convert.adapters.solidworks.Core.AssemblyPreparation.Children.ReadAsmPlanes import ReadAsmPlanes
from convert.adapters.solidworks.Core.AssemblyPreparation.Model.ReadAsmModel import ReadAsmModel
from convert.adapters.solidworks.Core.AssemblyPreparation.Paths.ReadAsmPaths import ReadAsmPaths
from convert.adapters.solidworks.Core.AssemblyPreparation.Placements.ReadAsmPlace import ReadAsmPlace
from convert.adapters.solidworks.Core.AssemblyPreparation.Recipe.MakeAsmRecipe import MakeAsmRecipe
from convert.adapters.solidworks.Core.Preparation.DefaultPartTree import DefaultPartTree
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from convert.adapters.solidworks.Core.Preparation.PrepareNative import PrepareNative
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorSpace import SpaceVector
from para.concentric.ConcentricMate import make_concentric
from para.cylinder.CylinderAttachment import GeneratedAttachment, attach_cylinder_mut


@dataclass(frozen=True)
class ConcentricBundle:
    attachment: GeneratedAttachment
    assembly: bytes


def principal_planes(document, written_at):
    if document.support_planes:
        return ReadAsmPlanes(document)
    result = {}
    for axis, name in DefaultPartTree("Front Plane", written_at).PlaneNames:
        frame = PrincipalFrame(axis)
        transform = Transform(SpaceVector(*frame.OriginValue), SpaceVector(*frame.AxisU),
                              SpaceVector(*frame.AxisV), SpaceVector(*frame.NormalValue))
        result[axis] = SupportPlane("native/principal/" + axis, name, transform)
    return result


def prepare_concentric(document, destination, written_at, session, updates, preceding_faces):
    model = ReadAsmModel(document)
    planes = principal_planes(document, written_at)
    paths = ReadAsmPaths(model.RootValue.name, model.ChildValue.name, destination, written_at)
    actual_child = model.ChildDocument
    if actual_child.brep is None:
        plain = actual_child
        profile = "derived_feature"
    else:
        plain = replace(actual_child, brep=None)
        profile = "authored_brep"
    settings = WriteOptions(values={"final_destination": paths.ChildValue.PathName})
    child_before_attachment = PrepareNative(plain, BytesIO(), written_at, settings)
    attached = attach_cylinder_mut(
        child_before_attachment, session, updates, preceding_faces, tessellated_faces=True,
    )
    nodes = {item.index: XmtNode(item.index, item.kind, item.fields) for item in attached.projection.partition.nodes}
    binding = bind_cylinder(actual_child, attached.candidate, nodes, profile=profile)
    intent = project_concentric(document, {model.ChildValue.id: binding})
    part_recipe = MakePartRecipe(attached.candidate.PlanValue, written_at)
    metadata = MakeAsmRecipe(intent.model, part_recipe, planes, paths.ParentValue)
    placements = tuple(ReadAsmPlace(value) for value in intent.model.Occurrences)
    selected = tuple(end.occurrence_index for end in intent.ends)
    state = MakeAsmBase(metadata)
    headers = MakeAsmHeaders(state, metadata)
    references = PutPartRefsMut(state, attached.candidate, metadata, placements, headers)
    mate = make_concentric(
        state, metadata, headers, tuple(references[index] for index in selected),
        tuple(end.placement.FrameValue for end in intent.ends), attached,
        intent.mate.name, intent.alignment_code, intent.rotation_locked, selected.index(intent.fixed_index),
    )
    streams = EmitAsmStreams(state, attached.candidate, metadata, headers, references, (mate,)).StreamsValue
    return ConcentricBundle(attached, BuildSldprt(streams, FormatVersion=4))
