from collections import Counter
from dataclasses import dataclass, replace
from pathlib import PureWindowsPath

from ColdEllipseModel import plan_ellipse
from EllipseModel import require
from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Archive.CmgrHeader.WriteMgrHeader import WriteMgrHeader
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Construction.Blind.BlindEndInput import BlindEndInput
from convert.adapters.solidworks.Archive.Construction.Configuration.SetCfgStampMut import SetCfgStampMut
from convert.adapters.solidworks.Archive.Construction.Extrusion.MakeBlindMut import MakeBlindMut
from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeBiography import MakeBiography
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeFreshHist import MakeFreshHist
from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.MakePartProps import MakePartProps
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import PersistentIds
from convert.adapters.solidworks.Archive.Construction.Part.CheckPartInput import CheckPartInput
from convert.adapters.solidworks.Archive.Construction.Part.MakePartBaseMut import MakePartBaseMut
from convert.adapters.solidworks.Archive.Construction.Part.MakePartHeaders import MakePartHeaders
from convert.adapters.solidworks.Archive.Construction.Part.MakePartKeys import MakePartKeys
from convert.adapters.solidworks.Archive.Construction.Profile.BeginProfileMut import BeginProfileMut
from convert.adapters.solidworks.Archive.Construction.Profile.MakeProfileData import MakeProfileData
from convert.adapters.solidworks.Archive.Construction.Profile.ProfileGraph import ProfileGraph
from convert.adapters.solidworks.Archive.Construction.Sketch.EntityFields import EntityFields
from convert.adapters.solidworks.Archive.Construction.Sketch.MakeRingPoint import MakeRingPoint
from convert.adapters.solidworks.Archive.Construction.Sketch.MakeSketchSeed import MakeSketchSeed
from convert.adapters.solidworks.Archive.Definition.Construction.MakePartDef import MakePartDef
from convert.adapters.solidworks.Archive.Definition.WriteModelDef import WriteModelDef
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.History.WriteHistMut import WriteHistMut
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import BuildSldprt
from convert.adapters.solidworks.Container.Format import KResolvedFeaturesStream, KeywordsStream
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe

VERSION = 19000


@dataclass(frozen=True, slots=True)
class ColdEllipseSketch:
    SketchValue: ArchiveNode
    PointValues: tuple[ArchiveNode, ...]
    SegmentValue: ArchiveNode


def reflect(center, point):
    return tuple(c - (p - c) for c, p in zip(center, point, strict=True))


def make_sketch(profile, plan):
    sketch = MakeSketchSeed(profile)
    c, major, minor = plan.CenterValue, plan.MajorValue, plan.MinorValue
    points_in_file = ("center", "seam", "major", "minor", "anti_major", "anti_minor")
    permanent_order = ("seam", "center", *points_in_file[2:])
    coordinates = dict(zip(points_in_file, (c, major, major, minor, reflect(c, major), reflect(c, minor)), strict=True))
    points = {key: MakeRingPoint(sketch, coordinates[key], index) for index, key in enumerate(permanent_order)}
    ordinals = {name: index for index, name in enumerate(points_in_file)}
    endpoints = ("seam", "seam")
    uses = Counter((*endpoints, "center", *points_in_file[2:]))
    segment = ArchiveNode(RuntimeClass("sgEllipse", 1), EntityFields(sketch) | {
        "_start": points[endpoints[0]], "_end": points[endpoints[1]],
        "f08": 1, "f0c": 1, "fc8_s": ordinals[endpoints[0]], "fcc_s": ordinals[endpoints[1]],
        "fd0": 1, "fd4": 0, "seg_tol": -1.0, "fd8": 1,
        **{field: ordinals[role] for field, role in zip(
            ("fdc_s", "fe0_s", "fe4_s", "fe8_s", "fec_s"), ("center", *points_in_file[2:]), strict=True)},
    })
    handle = ArchiveNode(RuntimeClass("sgEllipseHandle", 1),
                         {"_sketch": sketch, "_ellipse": segment, "idx": 0, "f1c": -1, "f08": 0})
    kinds = {"center": 0, "seam": 2}
    for role, point in points.items():
        point.FieldsValue.update(fe4=kinds.get(role, 3), fe8=uses[role], fec=int(role == "center"),
                                 h1=handle if role == "seam" else None)
    ordered = tuple(points[role] for role in points_in_file)
    ellipses = ({"flags": 0, "ellipse": segment.FieldsValue},)
    fields = sketch.FieldsValue
    fields.update(points=tuple({"kind": 0, "point": point.FieldsValue} for point in ordered), npoints=len(ordered),
                  ellipses=ellipses, nellipses=len(ellipses), f130=len(ellipses) + 1, f56c=len(ellipses) + 1)
    fields["f140"].update(f08=len(ordered) + 1, f14=len(ellipses) + 1)
    return ColdEllipseSketch(sketch, ordered, segment)


def emit(system, roots, headers, settings, plan):
    header, top, manager = headers
    config, config_graph = WriteConfigMut(system.RootValue, VERSION, header)
    context = {"model_compressed_stream": 1, "model_is_part": 1, "cmgr_f658": system.ManagerValue.FieldsValue["f658"]}
    resolved, resolved_graph = WriteResolMut(roots, {"n": 0, "fcd8": []}, VERSION, config_graph.MapValue, context,
                                             ReplayEllipses=True)
    definition = MakePartDef(settings.DefinitionValue, settings.DensityValue)
    streams = {
        "Header2": WriteHeadGraph(top, VERSION),
        "Contents/Config-0-ModelHeader": WriteHeadGraph(header, VERSION),
        "Contents/Config-0": config,
        "Contents/CMgr": WriteCmgrMut(system.ManagerValue, VERSION),
        "Contents/CMgrHdr2": WriteMgrHeader(manager, VERSION)[0],
        KResolvedFeaturesStream: resolved,
        "Contents/Definition": WriteModelDef(definition).OutputValue,
        "_MO_VERSION_19000/Biography": WriteHistMut(MakeBiography(), VERSION)[0],
        "_MO_VERSION_19000/History": WriteHistMut(MakeFreshHist(settings.HistoryValue), VERSION)[0],
        KeywordsStream: MakePartKeys(system, roots, settings, plan),
        **MakePartProps(settings.PropertiesValue),
    }
    return BuildSldprt(streams, FormatVersion=4), streams, config_graph, resolved_graph


def build(document, locator, epoch):
    plan = plan_ellipse(document)
    target = PureWindowsPath(locator)
    require(target.is_absolute() and target.drive == "C:" and ".." not in target.parts
            and target.name == plan.NameValue + ".SLDPRT" and type(epoch) is int and epoch > 0,
            "ellipse requires an actual owned native locator and explicit creation time")
    settings = replace(MakePartRecipe(plan, epoch), OutputValue=SelfFileInput(str(target), epoch))
    CheckPartInput(document, settings, plan)
    allocator = PersistentIds()
    system = MakePartBaseMut(settings, plan, allocator)
    support = system.SystemValues.PlaneValues[plan.AxisValue]
    profile, reference, frame = BeginProfileMut(plan.SketchName, system.RootValue, support, plan.AxisValue,
                                                settings.TargetValue, allocator)
    sketch = make_sketch(profile, plan)
    profile.FieldsValue.update(MakeProfileData(sketch.SketchValue, reference, frame))
    graph = ProfileGraph(profile, sketch, reference, frame)
    boss = MakeBlindMut(plan.FeatureName, system.RootValue, graph, BlindEndInput(plan.DepthValue, False, VERSION),
                        settings.TargetValue, allocator, settings.DesignIntent, settings.SelectedLeader)
    SetCfgStampMut(system.ConfigValues[0], allocator)
    system.ManagerValue.FieldsValue["f658"] = 1
    headers = MakePartHeaders(system, settings, allocator)
    roots = (*system.FeatureValues, profile, boss.FeatureValue)
    return (plan, *emit(system, roots, headers, settings, plan))
