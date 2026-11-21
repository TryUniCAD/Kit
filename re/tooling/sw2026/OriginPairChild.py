from __future__ import annotations

from DrawingSdkLinkedInput import part_settings
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import PersistentIds
from convert.adapters.solidworks.Archive.Construction.Part.CheckPartInput import CheckPartInput
from convert.adapters.solidworks.Archive.Construction.Part.FinishBlindMut import FinishBlindMut
from convert.adapters.solidworks.Archive.Construction.Part.MakePartBaseMut import MakePartBaseMut
from convert.adapters.solidworks.Archive.Construction.Part.MakePartProfMut import MakePartProfMut
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectRectDims import ProjectRectDims
from convert.adapters.solidworks.Archive.Construction.RectangleAnchors.MakeCornerMut import MakeCornerMut
from convert.adapters.solidworks.Archive.Construction.RectangleCenters.MakeCenterMut import MakeCenterMut
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakeRectDimsMut import MakeRectDimsMut
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakeSketchKeys import MakeSketchKeys
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.RectDimInput import RectDimInput
from interchange.document.Models.DocumentModel import CadDocument
from interchange.serialization.Deserialize import FromData


def make_child(job):
    policy = job["child_policy"]
    if set(policy) != {"kind", "width_text_m", "height_text_m", "route_centerline"} or policy["kind"] not in ("corner-anchored", "center-anchored"):
        raise ValueError("origin pair child construction requires a complete corner or centered anchor family")
    document = FromData(job["part"]["document"])
    if type(document) is not CadDocument:
        raise ValueError("origin pair requires an actual neutral child document")
    settings = part_settings(job)
    plan = ProjectRectDims(document)
    CheckPartInput(document, settings, plan)
    allocator = PersistentIds()
    system = MakePartBaseMut(settings, plan, allocator)
    profile = MakePartProfMut(system, settings, plan, allocator)
    inputs = RectDimInput(tuple(policy["width_text_m"]), tuple(policy["height_text_m"]),
                          settings.DesignIntent, settings.SelectedLeader, policy["route_centerline"])
    dimensions = MakeRectDimsMut(profile, inputs, allocator, plan.SketchDriverNames)
    if policy["kind"] == "corner-anchored":
        MakeCornerMut(profile, system.OriginValue)
    else:
        MakeCenterMut(profile, system.OriginValue)
    keys = MakeSketchKeys(dimensions, settings.DocumentUnits.LengthUnit)
    return FinishBlindMut(system, profile, settings, plan, allocator, keys), settings, keys
