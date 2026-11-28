from __future__ import annotations

from dataclasses import replace

from DrawingSdkLinkedInput import part_settings
from EpochClocks import ClockPlan, apply_before_emit, require
from convert.adapters.solidworks.Archive.Construction.Blind.BlindEndInput import BlindEndInput
from convert.adapters.solidworks.Archive.Construction.Configuration.SetCfgStampMut import SetCfgStampMut
from convert.adapters.solidworks.Archive.Construction.Extrusion.MakeBlindMut import MakeBlindMut
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import PersistentIds
from convert.adapters.solidworks.Archive.Construction.Part.CheckPartInput import CheckPartInput
from convert.adapters.solidworks.Archive.Construction.Part.EmitPartStreams import EmitPartStreams
from convert.adapters.solidworks.Archive.Construction.Part.MakePartBaseMut import MakePartBaseMut
from convert.adapters.solidworks.Archive.Construction.Part.MakePartHeaders import MakePartHeaders
from convert.adapters.solidworks.Archive.Construction.Part.MakePartProfMut import MakePartProfMut
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectRectDims import ProjectRectDims
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import PartCandidate
from convert.adapters.solidworks.Archive.Construction.RectangleAnchors.MakeCornerMut import MakeCornerMut
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakeRectDimsMut import MakeRectDimsMut
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakeSketchKeys import MakeSketchKeys
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.RectDimInput import RectDimInput
from convert.adapters.solidworks.Archive.Definition.Construction.MakePartDef import MakePartDef
from convert.adapters.solidworks.Container.Container import BuildSldprt
from interchange.document.Models.DocumentModel import CadDocument
from interchange.serialization.Deserialize import FromData


def make_epoch_child(job, clocks):
    require(type(clocks) is ClockPlan, "epoch child requires the explicit typed clock model")
    policy = job["child_policy"]
    require(set(policy) == {"kind", "width_text_m", "height_text_m", "route_centerline"}
            and policy["kind"] == "corner-anchored", "epoch discovery preserves the qualified corner-anchored child family")
    document = FromData(job["part"]["document"])
    require(type(document) is CadDocument, "epoch child requires an actual neutral document")
    settings = part_settings(job)
    plan = ProjectRectDims(document)
    CheckPartInput(document, settings, plan)
    allocator = PersistentIds()
    system = MakePartBaseMut(settings, plan, allocator)
    profile = MakePartProfMut(system, settings, plan, allocator)
    inputs = RectDimInput(tuple(policy["width_text_m"]), tuple(policy["height_text_m"]),
                          settings.DesignIntent, settings.SelectedLeader, policy["route_centerline"])
    dimensions = MakeRectDimsMut(profile, inputs, allocator, plan.SketchDriverNames)
    MakeCornerMut(profile, system.OriginValue)
    keys = MakeSketchKeys(dimensions, settings.DocumentUnits.LengthUnit)
    boss = MakeBlindMut(plan.FeatureName, system.RootValue, profile,
                        BlindEndInput(plan.DepthValue, False, 19000, plan.DepthName),
                        settings.TargetValue, allocator, settings.DesignIntent, settings.SelectedLeader)
    SetCfgStampMut(system.ConfigValues[0], allocator)
    headers = MakePartHeaders(system, settings, allocator)
    composition = apply_before_emit(headers, system.RootValue, clocks, settings)
    experimental = replace(settings, HistoryValue=replace(settings.HistoryValue,
                                                          CreatedAt=clocks.VersionHistoryFirstEventAt))
    definition = MakePartDef(settings.DefinitionValue, settings.DensityValue)
    features = (*system.FeatureValues, profile.ProfileValue, boss.FeatureValue)
    streams, config, resolved = EmitPartStreams(system, features, headers, definition,
                                                experimental, plan, keys)
    child = PartCandidate(system, profile, boss, headers[0], headers[1], headers[2],
                          definition, config, resolved, streams, BuildSldprt(streams, FormatVersion=4), plan)
    return child, experimental, keys, composition
