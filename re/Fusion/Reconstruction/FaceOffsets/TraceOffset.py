from interchange.Features.Offsets.FaceOffset import FaceOffset
from interchange.serialization.EncodeData import ToData
from dataclasses import asdict
import math

from convert.adapters.Fusion.Native.Graph.GraphChecks import LinkedNodes
from convert.adapters.Fusion.Native.Graph.GraphValues import NumberValue
from convert.Formats.Fusion.EntityCodec.Model.OptionalValue import OptionalValue
from convert.Formats.Fusion.EntityCodec.Recipes.Model.RecipeValue import RecipeValue
from convert.Formats.Fusion.EntityCodec.Recipes.Model.BoundFaceRecipe import BoundFaceRecipe
from convert.Formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.Planar.MakeLiveTable import MakeLiveTable
from convert.Formats.Fusion.BrepCodec.Journal.Planar.ReadBodyFaces import ReadBodyFaces
from convert.Formats.Fusion.BrepCodec.Journal.Planar.StableRef import StableRef


def trace_offset(graph, feature, history):
    parameter = graph.Resolve(feature.Fields['rParamDistance'])
    if graph.Resolve(parameter.Fields['rrOwnerFeature']) != feature:
        raise ValueError('Offset distance belongs to a different feature')
    distance = NumberValue(parameter.Fields['value'])
    target, = LinkedNodes(graph, feature, 'targetDataRefs')
    operand, = LinkedNodes(graph, target, 'dataRefs')
    body, = LinkedNodes(graph, operand, 'refBodies')
    recipe_node = graph.Resolve(operand.Fields['rRecipe'])
    saved = recipe_node.Fields['m_Recipe']
    if not isinstance(saved, OptionalValue) or not isinstance(saved.Value, RecipeValue) or not isinstance(saved.Value.Payload, BoundFaceRecipe):
        raise ValueError('Offset target is not a bound-face recipe')
    tag, = saved.Value.Tags[saved.Value.Payload.PrimaryTagIndex]
    label = FeatureTag(''.join(chr(value) for value in tag.PrimaryId), tag.OperationIds, tag.SecondaryId, tag.ApproachId)
    table = MakeLiveTable(history, feature.Fields['startModelHS'])
    body_ref, = (ref for ref in table.LiveSlots if isinstance(table.Entities[ref], BodyNode))
    faces = ReadBodyFaces(table, body_ref)
    owner, = (StableRef(table, entity.Links.OwnerRef) for ref in table.LiveSlots for entity in (table.Entities[ref],) if isinstance(entity, TagAttrib) and entity.Groups == (label,))
    face, = (face for face in faces if face.FaceRef == owner)
    normal = tuple((-1 if face.Reversed else 1) * value for value in face.Surface.Normal)
    axis, = (index for index, value in enumerate(normal) if math.isclose(abs(value), 1.0, abs_tol=1e-12))
    if any(abs(value) > 1e-12 for index, value in enumerate(normal) if index != axis):
        raise ValueError('Offset face is not axis aligned')
    return {'definition': ToData(FaceOffset(graph.Resolve(body.Fields['rBody']).Identity, target.Identity, graph.Resolve(parameter.Fields['parameter']).Identity)), 'feature_id': feature.Identity, 'parameter_id': parameter.Identity, 'distance_cm': distance, 'target_reference_id': target.Identity, 'operand_id': operand.Identity, 'body_id': body.Identity, 'recipe_id': recipe_node.Identity, 'selected_tag': asdict(label), 'face_ref': owner, 'outward_normal': normal, 'axis': axis, 'start_state': feature.Fields['startModelHS'], 'end_state': feature.Fields['endModelHS']}
