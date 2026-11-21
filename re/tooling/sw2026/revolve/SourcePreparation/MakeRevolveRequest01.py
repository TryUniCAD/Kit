from dataclasses import replace
from math import radians, tau

from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.Enums.EnumUnits import UnitSystem
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.Features.FeatureAngleRev import AngularRevolve
from interchange.Features.FeatureBody import DesignBody
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Selection import Selection, SelectPathElem
from interchange.geometry.Models.Sketch import Sketch, SketchEntity, SketchRelation, ConstraintRef
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordParameter import Parameter, ParameterValue
from interchange.Records.RecordSource import CadSource

from ReadRevolveInput01 import read_plan, require


def make_request(spec):
    require(set(spec) == {'name', 'radial_mm', 'axial_mm', 'axis_x_mm', 'axis_span_mm',
        'angle_deg', 'reverse', 'edit_angle_deg', 'created_at', 'self_path'},
        'revolve spec contains unowned or missing author inputs')
    ri, ro = spec['radial_mm']
    lo, hi = spec['axial_mm']
    x = spec['axis_x_mm']
    a, b = spec['axis_span_mm']
    points = ((x + ri, lo), (x + ro, lo), (x + ro, hi), (x + ri, hi))
    edge_ids = tuple('edge/' + str(index) for index in range(4))
    entities = tuple(SketchEntity(edge_ids[index], GeometryKind.KLine,
        LineGeometry(PlaneVector(*point), PlaneVector(*points[(index + 1) % 4])))
        for index, point in enumerate(points))
    axis_id = 'axis/selected'
    entities += (SketchEntity(axis_id, GeometryKind.KLine,
        LineGeometry(PlaneVector(x, a), PlaneVector(x, b)), construction=True),)
    relations = tuple(SketchRelation('relation/' + str(index),
        'horizontal' if index % 2 == 0 else 'vertical', (ConstraintRef(edge_id),))
        for index, edge_id in enumerate(edge_ids))
    sketch = Sketch('sketch/profile', 'RevolveSketch', 'plane/front', entities,
        constraints=relations, closed_profile_entity_ids=(edge_ids,))
    selection = Selection('selection/axis', 'Selected local construction axis',
        (SelectPathElem('sketch', sketch.id), SelectPathElem('sketch_entity', axis_id)))
    require(type(spec['reverse']) is bool, 'reverse author input must be an explicit boolean')
    angle = ParameterValue(radians(spec['angle_deg']), ValueKind.KAngle, 'rad')
    definition = AngularRevolve(selection.id, 'parameter/angle', SpaceVector(x, a, 0.0),
        SpaceVector(0.0, -1.0 if spec['reverse'] else 1.0, 0.0))
    feature = FeatureStep('feature/revolve', 'OrdinaryBossRevolve', FeatureKind.KRevolution, 0,
        sketch_id=sketch.id, parameter_ids=('parameter/angle',), operation=BooleanOp.KCreate,
        definition=definition, selection_ids=(selection.id,))
    document = CadDocument(CadSource('kit-neutral', '<authored-ordinary-revolve>', '0' * 64),
        (Configuration('configuration/default', 'Default', True),),
        (Parameter('parameter/angle', 'D1', angle, ParameterRole.KDriving, owner_id=feature.id),),
        (SupportPlane('plane/front', 'Front Plane', Transform()),), (sketch,), (selection,), (feature,),
        (DesignBody('body/revolve', feature.name, feature.id),),
        metadata={'name': spec['name']}, units=UnitSystem.KMillimeter)
    plan = read_plan(document)
    settings = replace(MakePartRecipe(plan, spec['created_at']),
        OutputValue=SelfFileInput(spec['self_path'], spec['created_at']))
    return document, settings


def native_model(spec):
    return {'name': spec['name'], 'split': 'discovery', 'plane': 'front',
        'radius_m': [value * 0.001 for value in spec['radial_mm']],
        'axial_m': [value * 0.001 for value in spec['axial_mm']],
        'axis_x_m': spec['axis_x_mm'] * 0.001,
        'axis_axial_m': [value * 0.001 for value in spec['axis_span_mm']],
        'angle_deg': spec['angle_deg'], 'reverse': spec['reverse'],
        'edit_angle_deg': spec['edit_angle_deg']}
