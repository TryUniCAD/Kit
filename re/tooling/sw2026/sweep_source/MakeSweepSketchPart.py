from dataclasses import dataclass, replace

from convert.adapters.solidworks.Archive.Construction.Configuration.SetCfgStampMut import SetCfgStampMut
from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordConfig import KeywordConfig
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordFeature import KeywordFeature
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeKeywords import MakeKeywords
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import PersistentIds
from convert.adapters.solidworks.Archive.Construction.Part.EmitPartArchive import EmitPartArchive
from convert.adapters.solidworks.Archive.Construction.Part.MakePartBaseMut import MakePartBaseMut
from convert.adapters.solidworks.Archive.Construction.Part.MakePartHeaders import MakePartHeaders
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakeSketchKeys import MakeSketchKeys
from convert.adapters.solidworks.Archive.Definition.Construction.MakePartDef import MakePartDef
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt, ReadNodeName
from convert.adapters.solidworks.Container.Container import BuildSldprt
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from MakeSweepSketches import make_sweep_profiles
from SweepModel import PATH, SECTION, SWEEP, require


@dataclass(frozen=True)
class SweepLabels:
    NameValue: str
    ConfigName: str = "Default"
    PlaneName: str = "Front Plane"
    AxisValue: str = "z"
    SketchName: str = PATH
    FeatureName: str = SWEEP


def make_context(name, density, epoch, locator):
    labels = SweepLabels(name)
    settings = MakePartRecipe(labels, epoch)
    if locator is not None:
        settings = replace(settings, OutputValue=SelfFileInput(locator, epoch))
    settings = replace(settings, DensityValue=density)
    allocator = PersistentIds()
    system = MakePartBaseMut(settings, labels, allocator)
    return labels, settings, allocator, system


def key_row(node, tag, dims=(), kind=None):
    return KeywordFeature(FieldInt(node.FieldsValue, "f08"), ReadNodeName(node),
                          node.ClassValue.NameValue if kind is None else kind, tag, dims, (), None, None)


def sketch_keys(system, profiles, settings):
    unit = settings.DocumentUnits.LengthUnit
    return (
        *(key_row(node, "Feature") for node in system.FeatureValues),
        key_row(profiles.section, "Sketch", MakeSketchKeys((profiles.section_d1,), unit)),
        key_row(profiles.path, "Sketch", MakeSketchKeys((profiles.path_d1,), unit)),
    )


def make_sketch_part(name, section_radius, path_radius, density, epoch, locator=None):
    labels, settings, allocator, system = make_context(name, density, epoch, locator)
    profiles = make_sweep_profiles(system, settings, allocator, section_radius, path_radius)
    require(ReadNodeName(profiles.section) == SECTION and ReadNodeName(profiles.path) == PATH,
            "generated sketch ownership differs from the declared intent")
    SetCfgStampMut(system.ConfigValues[0], allocator)
    headers = MakePartHeaders(system, settings, allocator)
    definition = MakePartDef(settings.DefinitionValue, settings.DensityValue)
    config = tuple(KeywordConfig(FieldInt(node.FieldsValue, "f08"), ReadNodeName(node), "")
                   for node in system.ConfigValues)
    keywords = MakeKeywords(labels.NameValue, epoch, config, sketch_keys(system, profiles, settings))
    streams, config, resolved = EmitPartArchive(
        system, (*system.FeatureValues, profiles.section, profiles.path), headers, definition, settings, keywords,
    )
    return BuildSldprt(streams, FormatVersion=4), streams, config, resolved
