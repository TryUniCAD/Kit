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


def make_reference(document, settings, dimensions, kind):
    plan = ProjectRectDims(document)
    CheckPartInput(document, settings, plan)
    allocator = PersistentIds()
    system = MakePartBaseMut(settings, plan, allocator)
    profile = MakePartProfMut(system, settings, plan, allocator)
    drivers = MakeRectDimsMut(profile, dimensions, allocator, plan.SketchDriverNames)
    if kind == 'corner':
        MakeCornerMut(profile, system.OriginValue)
    elif kind == 'center':
        MakeCenterMut(profile, system.OriginValue)
    else:
        raise ValueError('unknown complete anchor family')
    keys = MakeSketchKeys(drivers, settings.DocumentUnits.LengthUnit)
    return FinishBlindMut(system, profile, settings, plan, allocator, keys)
