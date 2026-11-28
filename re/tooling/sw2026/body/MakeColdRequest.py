from math import isfinite

from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
from convert.adapters.solidworks.Archive.Construction.Header.HeaderInput import HeaderInput
from convert.adapters.solidworks.Archive.Construction.Metadata.HistoryInput import HistoryInput
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import FeatureTarget
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import PartBuildInput
from convert.adapters.solidworks.Archive.Construction.Presentation.StyleInput import StyleInput
from convert.adapters.solidworks.Archive.Construction.System.SystemInput import SystemInput
from convert.adapters.solidworks.Archive.Construction.Units.UnitInput import UnitInput
from convert.adapters.solidworks.Archive.Definition.Construction.ModelDefSettings import ModelDefInput
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.Enums.EnumUnits import UnitSystem
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.Features.FeatureBody import DesignBody
from interchange.Features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Sketch import Sketch, SketchEntity
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordParameter import Parameter, ParameterValue
from interchange.Records.RecordSource import CadSource


def make_request(spec):
    if set(spec) != {'model_name', 'body_label', 'width_mm', 'height_mm', 'depth_mm',
                     'centre_xy_mm', 'edited_depth_mm', 'created_at', 'self_path'}:
        raise ValueError('cold source schema has unowned or missing inputs')
    numeric = tuple(spec[name] for name in ('width_mm', 'height_mm', 'depth_mm', 'edited_depth_mm'))
    if any(type(value) not in (float, int) or not isfinite(value) or not 1 < value < 200 for value in numeric):
        raise ValueError('cold source lengths are outside the finite analytic experiment')
    centre = spec['centre_xy_mm']
    if type(centre) is not list or len(centre) != 2 or any(type(value) not in (float, int) or not isfinite(value) or abs(value) > 100 for value in centre):
        raise ValueError('cold source has no explicit finite planar placement')
    if type(spec['created_at']) is not int or not 0 < spec['created_at'] < (1 << 31):
        raise ValueError('cold source needs an explicit representable authoring epoch')
    width, height, depth, _ = numeric
    x, y = centre
    vertices = ((x - width / 2, y - height / 2), (x + width / 2, y - height / 2),
                (x + width / 2, y + height / 2), (x - width / 2, y + height / 2))
    edge_ids = tuple('edge/' + str(index) for index in range(4))
    sketch = Sketch('sketch/profile', 'ColdSketch', 'plane/front', tuple(
        SketchEntity(edge_ids[index], GeometryKind.KLine,
                     LineGeometry(PlaneVector(*vertices[index]), PlaneVector(*vertices[(index + 1) % 4])))
        for index in range(4)), closed_profile_entity_ids=(edge_ids,))
    length = ParameterValue(depth, ValueKind.KLength, 'mm')
    feature = FeatureStep('feature/boss', 'ColdBoss', FeatureKind.KExtrusion, 0,
        sketch_id=sketch.id, parameter_ids=('parameter/depth',), operation=BooleanOp.KCreate,
        definition=ExtrudeFeature(length, ExtrudeEnd.KBlind, False, False))
    document = CadDocument(CadSource('kit-neutral', '<independent-cold-body-input>', '0' * 64),
        (Configuration('configuration/default', 'Default', True),),
        (Parameter('parameter/depth', 'D1', length, ParameterRole.KDriving, owner_id=feature.id),),
        (SupportPlane('plane/front', 'Front Plane', Transform()),), (sketch,), (), (feature,),
        (DesignBody('body/boss', spec['body_label'], feature.id),),
        metadata={'name': spec['model_name']}, units=UnitSystem.KMillimeter)
    folders = tuple(zip(('moCommentsFolder_c', 'moFavoriteFolder_c', 'moHistoryFolder_c',
        'moSelectionSetFolder_c', 'moSensorFolder_c', 'moDocsFolder_c', 'moSurfaceBodyFolder_c',
        'moSolidBodyFolder_c', 'moEnvFolder_c', 'moInkMarkupFolder_c', 'moEqnFolder_c', 'moMaterialFolder_c'),
        ('Comments', 'Favorites', 'History', 'Selection Sets', 'Sensors', 'Design Binder',
         'Surface Bodies', 'Solid Bodies', 'Environment', 'Markups', 'Equations', 'Material <not specified>'), strict=True))
    epoch = spec['created_at']
    units = UnitInput('mm', 'degree', 'mmgs', 4)
    style = StyleInput(1, 'Arial', 'authored continuous', 1033,
        (0.0001, 0.0002, 0.0003, 0.0004, 0.0005, 0.0006, 0.0007, 0.0008), (),
        ('description', 'high', 'low', 'complete', 'reminder'), ('item', 'description', 'stock'))
    settings = PartBuildInput(style, units, UnitInput('m', 'radian', 'mks', 4),
        SystemInput(folders, (('x', 'Right Plane'), ('y', 'Top Plane'), ('z', 'Front Plane')),
                    'Annotations', 'Origin', 'z', epoch, True), FeatureTarget(2026306, 370108),
        HeaderInput('Kit independent neutral author', 'generated body-name experiment',
                    'cold atom ownership without transmitted geometry', epoch, epoch + 10, epoch + 10),
        HistoryInput(epoch, 'cold atom ownership without transmitted geometry', 2026001, 0, 1033, False),
        ModelDefInput('moISO_c', (), (26, 4, 25, True), False, 'authored cold name journal', 19000),
        SelfFileInput(spec['self_path'], epoch + 20), 'ANSI31 (Iron BrickStone)', 'Configurations',
        1000.0, False, 0)
    return document, settings


def prediction(spec):
    width, height, depth = (spec[name] * 0.001 for name in ('width_mm', 'height_mm', 'depth_mm'))
    x, y = (value * 0.001 for value in spec['centre_xy_mm'])

    def prism(length):
        return {'body_count': 1, 'volume_m3': width * height * length,
            'area_m2': 2 * (width * height + (width + height) * length),
            'mass_kg': width * height * length,
            'centre_of_mass_m': [x, y, length / 2]}

    points = [[x - width / 2, y - height / 2, 0.0], [x + width / 2, y - height / 2, 0.0],
              [x + width / 2, y + height / 2, 0.0], [x - width / 2, y + height / 2, 0.0]]
    return {'intent': {'model_name': spec['model_name'], 'self_path': spec['self_path'],
        'configuration_name': 'Default', 'profile': 'ColdSketch', 'feature': 'ColdBoss',
        'support': 'Front Plane', 'vertices_m': points, 'sketch_lines': 4,
        'fixed_relations_in_user_sketch': 0, 'resolved_roots': 19, 'depth_m': depth},
        'edit': {'dimension': 'D1@ColdBoss', 'new_depth_m': spec['edited_depth_mm'] * 0.001,
                 'expected': prism(spec['edited_depth_mm'] * 0.001)},
        'expected_initial': prism(depth), 'body_label': spec['body_label']}
