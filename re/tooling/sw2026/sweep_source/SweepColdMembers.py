from dataclasses import replace

from convert.adapters.solidworks.Archive.Construction.Chronology.FeatureInstant import FeatureInstant
from convert.adapters.solidworks.Archive.Construction.System.Members.AttachMembers import AttachMembers
from convert.adapters.solidworks.Archive.Construction.System.Members.LightInput import LightInput
from convert.adapters.solidworks.Archive.Construction.System.Members.MemberInput import MemberInput
from convert.adapters.solidworks.Archive.Construction.System.Members.NotesInput import NotesInput
from SweepModel import require


def authored_members(system, settings, allocator, epoch):
    created = FeatureInstant(epoch, 0)
    ambient = LightInput("ambient", "Ambient", "SweepAmbient", 0.5, 0.5, 0.0, 0xffffff,
                         True, False, True, 1.0, True, 16.0, None, None, created)
    directions = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    lights = tuple(LightInput("directional", f"Directional{index}", f"SweepLight{index}", 0.0, 0.5, 0.25,
                              0xffffff, True, False, True, 1.0, True, 16.0, direction, 0.5, created)
                   for index, direction in enumerate(directions, 1))
    notes = NotesInput("Notes", "Notes1___EndTag___", created, created)
    AttachMembers(system, MemberInput(notes, (ambient, *lights)), settings.TargetValue, allocator)
    cabinet = system.SystemValues.CabinetValue
    surface = system.SystemValues.FolderValues["moSurfaceBodyFolder_c"]
    roots = tuple(node for node in system.FeatureValues if node is not cabinet)
    require(len(roots) + 1 == len(system.FeatureValues), "expected one actual model annotation cabinet")
    offset = roots.index(surface)
    return replace(system, FeatureValues=(*roots[:offset], cabinet, *roots[offset:]))
