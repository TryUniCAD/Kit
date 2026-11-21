from hashlib import sha256
import json

from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.Enums.EnumUnits import UnitSystem
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.Features.FeatureBody import DesignBody
from interchange.Features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.GeometryCurves import CircleGeometry
from interchange.geometry.Models.Sketch import ConstraintRef, Sketch, SketchEntity, SketchRelation
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordParameter import Parameter, ParameterValue
from interchange.Records.RecordSource import CadSource


def make_document(spec):
    radius = float(spec['radius_mm'])
    center = tuple(float(value) for value in spec['center_mm'])
    length = ParameterValue(float(spec['depth_mm']), ValueKind.KLength, 'mm')
    radial = ParameterValue(radius * (2 if spec['driver'] == 'diameter' else 1), ValueKind.KLength, 'mm')
    entity = SketchEntity('geometry/circle', GeometryKind.KCircle, CircleGeometry(PlaneVector(*center), radius))
    sketch = Sketch('sketch/round', 'RoundProfile', 'datum/support', (entity,),
        parameter_ids=('driver/radial',),
        constraints=(
            SketchRelation('rule/center', 'fixed', (ConstraintRef(entity.id, 'center'),)),
            SketchRelation('rule/radial', spec['driver'], (ConstraintRef(entity.id),), 'driver/radial'),
        ), closed_profile_entity_ids=((entity.id,),))
    feature = FeatureStep('feature/round', 'RoundBoss', FeatureKind.KExtrusion, 0,
        sketch_id=sketch.id, parameter_ids=('driver/depth',), operation=BooleanOp.KCreate,
        definition=ExtrudeFeature(length=length, end_condition=ExtrudeEnd.KBlind,
            reversed=bool(spec['reversed']), symmetric=False))
    frame = Transform() if spec['axis'] == 'z' else Transform(
        SpaceVector(0, 0, 0), SpaceVector(1, 0, 0), SpaceVector(0, 0, -1), SpaceVector(0, 1, 0))
    request_sha = sha256(json.dumps(spec, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    return CadDocument(
        CadSource('kit-neutral', '<independent-authored-cylinder>', request_sha),
        (Configuration('config/default', 'Default', True),),
        (Parameter('driver/depth', 'D1', length, ParameterRole.KDriving, owner_id=feature.id),
         Parameter('driver/radial', 'D1', radial, ParameterRole.KDriving, owner_id=sketch.id)),
        (SupportPlane('datum/support', spec['plane'], frame),), (sketch,), (), (feature,),
        (DesignBody('body/round', feature.name, feature.id),),
        metadata={'name': spec['name']}, units=UnitSystem.KMillimeter)
