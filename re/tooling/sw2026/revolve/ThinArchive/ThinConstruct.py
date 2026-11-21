from dataclasses import replace
from math import degrees, copysign
from struct import pack

from convert.adapters.solidworks.Archive.Construction.Configuration.SetCfgStampMut import SetCfgStampMut
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeDimValue import MakeDimValue
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeHandleMut import MakeHandleMut
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakePoint import MakePoint
from convert.adapters.solidworks.Archive.Construction.Extrusion.MakeExtrusionView import MakeExtrudeView
from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
from convert.adapters.solidworks.Archive.Construction.Geometry.FrameXform import FrameXform
from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import PlaneFrame
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordConfig import KeywordConfig
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordDim import KeywordDim
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordFeature import KeywordFeature
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeKeywords import MakeKeywords
from convert.adapters.solidworks.Archive.Construction.Nodes.InitNodeMut import InitNodeMut
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import PersistentIds
from convert.adapters.solidworks.Archive.Construction.Part.CheckPartInput import CheckPartInput
from convert.adapters.solidworks.Archive.Construction.Part.MakePartBaseMut import MakePartBaseMut
from convert.adapters.solidworks.Archive.Construction.Part.MakePartHeaders import MakePartHeaders
from convert.adapters.solidworks.Archive.Construction.Profile.BeginProfileMut import BeginProfileMut
from convert.adapters.solidworks.Archive.Construction.Profile.MakeProfileData import MakeProfileData
from convert.adapters.solidworks.Archive.Construction.Profile.ProfileGraph import ProfileGraph
from convert.adapters.solidworks.Archive.Construction.Revolves.Feature.MakeRevFeatMut import MakeRevFeatMut
from convert.adapters.solidworks.Archive.Construction.Revolves.Part.EmitRevStreams import EmitRevStreams
from convert.adapters.solidworks.Archive.Construction.Sketch.MakeLineHandle import MakeLineHandle
from convert.adapters.solidworks.Archive.Construction.Sketch.MakeRingLine import MakeRingLine
from convert.adapters.solidworks.Archive.Construction.Sketch.MakeRingPoint import MakeRingPoint
from convert.adapters.solidworks.Archive.Construction.Sketch.MakeSketchSeed import MakeSketchSeed
from convert.adapters.solidworks.Archive.Construction.Sketch.PolygonGraph import PolygonGraph
from convert.adapters.solidworks.Archive.Definition.Construction.MakePartDef import MakePartDef
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt, ReadNodeName
from convert.adapters.solidworks.Container.Container import BuildSldprt
from convert.adapters.solidworks.Container.Format import KeywordsStream
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe

from ThinNeutral import plan_thin


def make_open_profile(system, settings, plan, ids):
    node, reference, frame = BeginProfileMut(
        plan.SketchName, system.RootValue, system.SystemValues.PlaneValues[plan.AxisValue],
        plan.AxisValue, settings.TargetValue, ids)
    sketch = MakeSketchSeed(node)
    coordinates = (*plan.VerticesValue, plan.AxisStart, plan.AxisEnd)
    points = tuple(MakeRingPoint(sketch, pos, index) for index, pos in enumerate(coordinates))
    body, axis = (MakeRingLine(sketch, points, index) for index in (0, 2))
    lines = (body, axis)
    main_flag = 0x40
    centreline_flag = 8
    for index, (line, flag) in enumerate(zip(lines, (main_flag, centreline_flag), strict=True)):
        line.FieldsValue.update(f08=len(lines) - index, f0c=index + 1,
                                f54=FieldInt(line.FieldsValue, "f54") | flag,
                                fd0=int(line is body))
        for pt in points[2 * index:2 * index + 2]:
            pt.FieldsValue.update(h1=MakeLineHandle(sketch, line, index), fe8=1)
    sketch.FieldsValue.update(points=tuple({"kind": 0, "point": p.FieldsValue} for p in points),
                              lines=tuple({"flags": 2 if l is axis else 0, "line": l.FieldsValue} for l in lines),
                              npoints=len(points), nlines=len(lines), f130=len(lines) + 1, f56c=len(lines) + 1)
    sketch.FieldsValue["f140"].update(f08=len(points) + 1, f0c=len(lines) + 1)
    node.FieldsValue.update(MakeProfileData(sketch, reference, frame))
    return ProfileGraph(node, PolygonGraph(sketch, points, lines), reference, frame), axis


def wall_points(plan, mode, widths):
    (x, a), (_, b) = plan.VerticesValue
    y = (a + b) / 2
    first, second = widths
    start, stop = {0: (x, x + first), 1: (x, x - first), 2: (x - first / 2, x + first / 2),
                   3: (x, x + first)}[mode]
    return ((start, stop, y), (x, x - second, y) if mode == 3 else None)


def place_wall(dimension, anchors):
    start, stop, y = anchors
    sign = copysign(1.0, stop - start)
    basis_u, basis_v, basis_w = (sign, 0, 0), (0, 0, sign), (0, -1, 0)
    frame = PlaneFrame((start, y, 0.0), basis_u, basis_v, basis_w)
    dimension.FieldsValue.update(f80=MakePoint(XValue=start, YValue=y), fa0=MakePoint(XValue=stop, YValue=y),
        has_fe0=1, fe0=MakePoint(XValue=sign), fe8=MakePoint(ZValue=sign), has_ff0=1, ff0=FrameXform(frame))


def make_wall(feature, settings, ids, name, value, endpoints):
    parameter = ArchiveNode(RuntimeClass("moLengthParameter_c", 1), {})
    InitNodeMut(parameter, name)
    parameter.FieldsValue.update(owner=feature, f0c=0, f48=None, f58=value, f68=0)
    dimension = MakeDimValue(feature, parameter)
    ids.AllocateMut(dimension, "f50")
    if endpoints is not None:
        place_wall(dimension, endpoints)
    handle = MakeHandleMut(feature, dimension)
    display = MakeExtrudeView(feature, handle, False, settings.DesignIntent, settings.SelectedLeader)
    display.FieldsValue["f5b0"]["data"] = pack("<d", value)
    return display


def make_thin_spec(feature, settings, ids, plan, mode, widths):
    displays = tuple(make_wall(feature, settings, ids, name, value, endpoints)
                     for name, value, endpoints in zip(("D3", "D4"), widths, wall_points(plan, mode, widths), strict=True))
    return ArchiveNode(RuntimeClass("moThinSpec_c", 1), {
        "f08": displays[0], "f10": displays[1], "f2c": 0, "f30": -2.0, "f38": -2.0, "f28": mode,
        "f40": 1, "f48": None, "f50": 0, "f54": 0,
    })


def make_thin_keys(system, roots, settings, plan, widths, mode):
    configs = tuple(KeywordConfig(FieldInt(node.FieldsValue, "f08"), ReadNodeName(node), "")
                    for node in system.ConfigValues)
    features = tuple(KeywordFeature(FieldInt(node.FieldsValue, "f08"), ReadNodeName(node),
                                    node.ClassValue.NameValue, "Feature", (), (), None, None) for node in roots[:-2])
    profile, feature = roots[-2:]
    angle = KeywordDim("D1", degrees(plan.AngleValue), "degree")
    first = KeywordDim("D3", 1000 * widths[0], None)
    drivers = (angle, KeywordDim("D4", 1000 * widths[1], None), first) if mode == 3 else (first, angle)
    features += (KeywordFeature(FieldInt(feature.FieldsValue, "f08"), ReadNodeName(feature),
                                "Revolve-Thin", "Feature", drivers, (), None, None),
                 KeywordFeature(FieldInt(profile.FieldsValue, "f08"), ReadNodeName(profile),
                                None, "Sketch", (), (), True, None))
    return MakeKeywords(plan.NameValue, settings.HeaderValue.ModifiedAt, configs, features)


def construct(doc, wall_mode, locator, epoch):
    plan, mode, widths = plan_thin(doc, wall_mode)
    settings = replace(MakePartRecipe(plan, epoch), OutputValue=SelfFileInput(locator, epoch))
    CheckPartInput(doc, settings, plan)
    ids = PersistentIds()
    system = MakePartBaseMut(settings, plan, ids)
    profile, axis = make_open_profile(system, settings, plan, ids)
    feature, _, _, _ = MakeRevFeatMut(system, profile, axis, settings, plan, ids, IsThin=True)
    feature.FieldsValue["f8f0"] = make_thin_spec(feature, settings, ids, plan, mode, widths)
    SetCfgStampMut(system.ConfigValues[0], ids)
    headers = MakePartHeaders(system, settings, ids)
    definition = MakePartDef(settings.DefinitionValue, settings.DensityValue)
    roots = (*system.FeatureValues, profile.ProfileValue, feature)
    streams, _, _ = EmitRevStreams(system, roots, headers, definition, settings, plan)
    streams[KeywordsStream] = make_thin_keys(system, roots, settings, plan, widths, mode)
    return BuildSldprt(streams, FormatVersion=4), plan
