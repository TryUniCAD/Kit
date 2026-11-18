from struct import pack

from convert.adapters.solidworks.Archive.Construction.Dimensions.DimensionGraph import DimensionGraph
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeHandleMut import MakeHandleMut
from convert.adapters.solidworks.Archive.Construction.Extrusion.MakeAngleValue import MakeAngleValue
from convert.adapters.solidworks.Archive.Construction.Extrusion.MakeExtrusionView import MakeExtrusionView
from convert.adapters.solidworks.Archive.Construction.Nodes.AtomSeeds import KAtomLists, KAtomWords
from convert.adapters.solidworks.Archive.Construction.Nodes.InitFeatureMut import InitFeatureMut
from convert.adapters.solidworks.Archive.Construction.Nodes.InitNodeMut import InitNodeMut
from convert.adapters.solidworks.Archive.Construction.PlanarMates.CompRefFields import CompRefFields
from convert.adapters.solidworks.Archive.Construction.Profile.MakeProfileMut import MakeProfileMut
from convert.adapters.solidworks.Archive.Construction.Profile.ProfileGraph import ProfileGraph
from convert.adapters.solidworks.Archive.Construction.Sketch.MakeLineHandle import MakeLineHandle
from convert.adapters.solidworks.Archive.Construction.Sketch.MakeRingPoint import MakeRingPoint
from convert.adapters.solidworks.Archive.Construction.Sketch.MakeRingLine import MakeRingLine
from convert.adapters.solidworks.Archive.Construction.Sketch.PolygonGraph import PolygonGraph
from convert.adapters.solidworks.Archive.Construction.Sketch.PolygonInput import PolygonInput
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakeAxisDim import MakeAxisDim
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.PublishRectMut import PublishRectMut
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


def make_profile(system, settings, plan, allocator):
    profile = MakeProfileMut(plan.SketchName, system.RootValue,
        system.SystemValues.PlaneValues['z'], 'z', PolygonInput(plan.VerticesValue, 19000),
        settings.TargetValue, allocator)
    geometry = profile.GeometryValue
    sketch = geometry.SketchValue
    points = (*geometry.PointValues, MakeRingPoint(sketch, plan.AxisStart, 4),
        MakeRingPoint(sketch, plan.AxisEnd, 5))
    axis = MakeRingLine(sketch, points, 4)
    axis.FieldsValue.update({'f54': axis.FieldsValue['f54'] | 8, 'fd0': 0})
    lines = (*geometry.LineValues, axis)
    for point in points[-2:]:
        point.FieldsValue.update({'h1': MakeLineHandle(sketch, axis, 4), 'h2': None, 'fe8': 1})
    fields = sketch.FieldsValue
    fields.update({'points': tuple({'kind': 0, 'point': point.FieldsValue} for point in points),
        'lines': tuple({'flags': 2 if line is axis else 0, 'line': line.FieldsValue} for line in lines),
        'npoints': len(points), 'nlines': len(lines), 'f130': len(lines) + 1,
        'f56c': len(lines) + 1})
    fields['f140'].update({'f08': len(points) + 1, 'f0c': len(lines) + 1})
    result = ProfileGraph(profile.ProfileValue, PolygonGraph(sketch, points, lines),
        profile.ReferenceValue, profile.FrameValue)
    logical = []
    for index, line in enumerate(geometry.LineValues):
        relation = MakeAxisDim(result.GeometryValue, index)
        start = plan.VerticesValue[index]
        end = plan.VerticesValue[(index + 1) % 4]
        relation['f80'] = 4 if start[1] == end[1] else 5
        logical.append(relation)
    PublishRectMut(result, (), tuple(logical), allocator, system.RootValue.FieldsValue['fd44'])
    return result, axis


def make_axis_reference(system, profile, axis, plan):
    sketch = profile.GeometryValue.SketchValue
    fields = CompRefFields(system.RootValue.FieldsValue['f990'])
    fields.update({'ff0': {'f00': profile.ProfileValue.FieldsValue['f08'], 'f08': 2592000},
        'f0f8': MakeLineHandle(sketch, axis, len(profile.GeometryValue.LineValues) - 1),
        'f100': axis.FieldsValue['f08']})
    selected = ArchiveNode(RuntimeClass('moCompSketchEntHandle_c', 1), fields)
    return ArchiveNode(RuntimeClass('moLineRef_w', 1), {
        'f58': selected, 'f60': None, 'f68': 0, 'f6c': 0, 'f08': 101,
        'has_f10': 0, 'has_f18': 0, 'f0c': -1, 'f20': 0,
        'f74': -12345, 'f78': -12345, 'f7c': -12345, 'f50': 0, 'f70': 19000,
        'f34': 0, 'f30': 0, 'f98': 0, 'f38': -1,
        'fc8': {'x': plan.AxisStart[0], 'y': plan.AxisStart[1], 'z': 0.0},
        'fe0': {'x': 0.0, 'y': 1.0, 'z': 0.0}, 'ff8': 0,
        'fb0': 0.0, 'fb8': plan.AxisEnd[1] - plan.AxisStart[1]})


def make_angle(feature, settings, plan, allocator):
    parameter = ArchiveNode(RuntimeClass('moAngleParameter_c', 1), {})
    InitNodeMut(parameter, 'D1')
    parameter.FieldsValue.update({'owner': feature, 'f0c': 0, 'f48': None,
        'f58': plan.AngleValue, 'f68': 0})
    dimension = MakeAngleValue(feature, parameter)
    allocator.AllocateMut(dimension, 'f50')
    handle = MakeHandleMut(feature, dimension)
    display = MakeExtrusionView(feature, handle, True, settings.DesignIntent, settings.SelectedLeader)
    display.FieldsValue['f5b0']['data'] = pack('<d', plan.AngleValue)
    return DimensionGraph(parameter, dimension, handle, display)


def make_feature(system, profile, axis, settings, plan, allocator):
    feature = ArchiveNode(RuntimeClass('moRevolution_c', 1), {})
    InitFeatureMut(feature, plan.FeatureName, system.RootValue, settings.TargetValue, allocator)
    feature.FieldsValue.update(dict.fromkeys(KAtomWords, 0))
    feature.FieldsValue.update({name: [] for name in KAtomLists})
    feature.FieldsValue.update({'f35c': 0, 'f368': {'n': 0, 'items': []},
        'f388': {'n': 0, 'items': []}, 'f538': None, 'f4a0': 1,
        'f6e0': None, 'f758': None, 'f780': {'n': 0, 'items': []}, 'f7a0': 0})
    reference = make_axis_reference(system, profile, axis, plan)
    angle = make_angle(feature, settings, plan, allocator)
    end = ArchiveNode(RuntimeClass('moRevEndSpec_c', 1), {
        'f08': 1, 'f138': 0, 'f13c': 0, 'f0c': 0, 'f10': 0,
        'f118': None, 'f120': None, 'f128': None, 'f130': None,
        'f38': 0.01, 'f40': 0.01, 'f140': 0, 'f144': 0,
        'f18': angle.DisplayValue, 'f20': None, 'f28': None, 'f30': None,
        'owner': feature})
    feature.FieldsValue.update({'f60': {'list': {'n': 1, 'items': [{'o': profile.ProfileValue}]}, 'tail': 0},
        'f808': None, 'f824': int(plan.IsReverse), 'f810': None, 'f820': 0,
        'f818': ArchiveNode(RuntimeClass('suObList', 1), {'n': 0, 'items': []}),
        'f828': 3, 'f870': 1, 'f830': reference, 'f8d8': end, 'f8e8': 0})
    return feature, reference, end, angle
