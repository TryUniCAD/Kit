from convert.adapters.solidworks.Archive.Construction.Configuration.SetCfgStampMut import SetCfgStampMut
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordConfig import KeywordConfig
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeKeywords import MakeKeywords
from convert.adapters.solidworks.Archive.Construction.Nodes.AtomSeeds import KAtomLists, KAtomWords
from convert.adapters.solidworks.Archive.Construction.Nodes.InitFeatureMut import InitFeatureMut
from convert.adapters.solidworks.Archive.Construction.Part.EmitPartArchive import EmitPartArchive
from convert.adapters.solidworks.Archive.Construction.Part.MakePartHeaders import MakePartHeaders
from convert.adapters.solidworks.Archive.Definition.Construction.MakePartDef import MakePartDef
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt, ReadNodeName
from convert.adapters.solidworks.Container.Container import BuildSldprt
from MakeSweepCurveRefs import curve_reference, node, object_rows, path_contact
from MakeSweepGhostPair import make_sweep_ghost_pair
from MakeSweepSketches import make_sweep_profiles
from MakeSweepSketchPart import key_row, make_context, sketch_keys
from SweepColdMembers import authored_members
from SweepGhostGraph import GHOST_STREAM
from SweepModel import SWEEP, require
from SweepReplay import sweep_replay


def make_sweep_node(system, profiles, settings, allocator):
    sweep = node("moSweep_c", {})
    part = system.RootValue
    InitFeatureMut(sweep, SWEEP, part, settings.TargetValue, allocator)
    fields = sweep.FieldsValue
    fields.update(dict.fromkeys(KAtomWords, 0))
    fields.update({key: [] for key in KAtomLists})
    fields.update({
        "f28": fields["f28"] | 2 | 0x4000,
        "f60": {"list": object_rows(profiles.section, profiles.path), "tail": 0},
        "f35c": 0, "f368": object_rows(), "f388": object_rows(), "f538": None, "f4a0": 1,
        "f544": 1, "f6e0": None, "f758": None, "f780": object_rows(), "f7a0": 0,
        "fc0c": 0, "fc10": 1, "fc14": 1, "fc18": 1, "fc1c": 1, "f80c": 1, "fc20": 0, "fc24": 1,
    })
    return sweep


def sweep_data(section, path):
    return {
        "f2c0": object_rows(section), "f2e0": object_rows(path_contact(path)), "f300": object_rows(),
        "f270": 0, "f274": 0, "f278": 0, "f70": 1.0, "f2ac": 0, "f2b0": 0, "f7c": 0, "f80": 0,
        "f98": object_rows(), "fe0": object_rows(), "f230": 0, "f78": 0, "f234": 0,
        "f238": 0.0, "f240": 0.0, "f248": 0, "f24c": 1, "f2b4": 0,
        "f280": 0.0, "f288": 0.0, "f290": 0, "f27c": 0, "f2a8": 0, "f258": 0, "f260": 0.0,
        "f298": None, "f2a0": None, "f2b8": 0, "f320": object_rows(), "f340": object_rows(), "f3b0": 0,
    }


def make_cold_sweep_part(name, section_radius, path_radius, density, epoch, locator=None):
    labels, settings, allocator, system = make_context(name, density, epoch, locator)
    system = authored_members(system, settings, allocator, epoch)
    profiles = make_sweep_profiles(system, settings, allocator, section_radius, path_radius)
    sweep = make_sweep_node(system, profiles, settings, allocator)
    section_value = profiles.section_d1.ParameterValue.FieldsValue["f58"]
    path_value = profiles.path_d1.ParameterValue.FieldsValue["f58"]
    require((section_value / 2, path_value) == (section_radius, path_radius), "sweep supports changed their driving values")
    pair = make_sweep_ghost_pair(system.RootValue, sweep, section_value / 2, path_value)
    system.RootValue.FieldsValue["fd90"] = pair.manager
    SetCfgStampMut(system.ConfigValues[0], allocator)
    headers = MakePartHeaders(system, settings, allocator)
    section = curve_reference(system, headers[0], profiles.section, "x", pair.section_id, profiles.section_d1)
    path = curve_reference(system, headers[0], profiles.path, "z", pair.path_id, profiles.path_d1)
    sweep.FieldsValue["f820"] = sweep_data(section, path)
    definition = MakePartDef(settings.DefinitionValue, settings.DensityValue)
    cfg_rows = tuple(KeywordConfig(FieldInt(item.FieldsValue, "f08"), ReadNodeName(item), "")
                     for item in system.ConfigValues)
    keys = (*sketch_keys(system, profiles, settings), key_row(sweep, "Feature", kind="Sweep"))
    keywords = MakeKeywords(labels.NameValue, epoch, cfg_rows, keys)
    with sweep_replay(cold=True):
        streams, cfg, resolved = EmitPartArchive(
            system, (*system.FeatureValues, profiles.section, profiles.path, sweep),
            headers, definition, settings, keywords,
        )
    streams[GHOST_STREAM] = pair.stream
    return BuildSldprt(streams, FormatVersion=4), streams, cfg, resolved
