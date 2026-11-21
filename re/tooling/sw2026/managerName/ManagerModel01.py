from convert.adapters.solidworks.Archive.Construction.Configuration.ConfigSpec import ConfigSpec
from convert.adapters.solidworks.Archive.Construction.Configuration.ManagerInput import ManagerInput
from convert.adapters.solidworks.Archive.Construction.Configuration.SetCfgStampMut import SetCfgStampMut
from convert.adapters.solidworks.Archive.Construction.Model.PartRootInput import PartRootInput
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import PersistentIds
from convert.adapters.solidworks.Archive.Construction.Part.CheckPartInput import CheckPartInput
from convert.adapters.solidworks.Archive.Construction.Part.MakePartHeaders import MakePartHeaders
from convert.adapters.solidworks.Archive.Construction.Presentation.MakePartRefs import MakePartRefs
from convert.adapters.solidworks.Archive.Construction.Revolves.Feature.MakeRevFeatMut import MakeRevFeatMut
from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.ProjectRevolve import ProjectRevolve
from convert.adapters.solidworks.Archive.Construction.Revolves.Part.EmitRevStreams import EmitRevStreams
from convert.adapters.solidworks.Archive.Construction.Revolves.Part.RevolvePart import RevolvePart
from convert.adapters.solidworks.Archive.Construction.Revolves.Sketch.MakeRevProfMut import MakeRevProfMut
from convert.adapters.solidworks.Archive.Construction.System.MakePartSysMut import MakePartSysMut
from convert.adapters.solidworks.Archive.Definition.Construction.MakePartDef import MakePartDef
from convert.adapters.solidworks.Container.Container import BuildSldprt


def make_system(settings, plan, manager_input, allocator):
    references = MakePartRefs(settings.StyleValue, settings.DocumentUnits, settings.AnalysisUnits)
    return MakePartSysMut(PartRootInput(plan.NameValue, settings.HatchName, 19000), references, manager_input, settings.SystemValue, settings.TargetValue, allocator)


def compose(document, settings, manager_name):
    plan = ProjectRevolve(document)
    CheckPartInput(document, settings, plan)
    if settings.PropertiesValue is not None or settings.DocumentUnits.AngleUnit != 'degree':
        raise ValueError('ordinary revolve construction requires degree presentation and no optional properties')
    allocator = PersistentIds()
    manager_input = ManagerInput(manager_name, (ConfigSpec(plan.ConfigName, '', settings.HeaderValue.ModifiedAt),), 0)
    system = make_system(settings, plan, manager_input, allocator)
    profile, axis = MakeRevProfMut(system, settings, plan, allocator)
    feature, reference, end, angle = MakeRevFeatMut(system, profile, axis, settings, plan, allocator)
    SetCfgStampMut(system.ConfigValues[0], allocator)
    headers = MakePartHeaders(system, settings, allocator)
    definition = MakePartDef(settings.DefinitionValue, settings.DensityValue)
    features = (*system.FeatureValues, profile.ProfileValue, feature)
    streams, config, resolved = EmitRevStreams(system, features, headers, definition, settings, plan)
    return RevolvePart(system, profile, feature, reference, end, angle, headers, definition, config, resolved, streams, BuildSldprt(streams, FormatVersion=4), plan, settings)
