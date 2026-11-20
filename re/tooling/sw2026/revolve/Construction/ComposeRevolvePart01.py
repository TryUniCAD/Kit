from dataclasses import dataclass
from math import degrees

from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Archive.CmgrHeader.WriteMgrHeader import WriteMgrHeader
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Construction.Configuration.SetCfgStampMut import SetCfgStampMut
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordConfig import KeywordConfig
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordDim import KeywordDim
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordFeature import KeywordFeature
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeBiography import MakeBiography
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeFreshHist import MakeFreshHist
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeKeywords import MakeKeywords
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import PersistentIds
from convert.adapters.solidworks.Archive.Construction.Part.CheckPartInput import CheckPartInput
from convert.adapters.solidworks.Archive.Construction.Part.MakePartBaseMut import MakePartBaseMut
from convert.adapters.solidworks.Archive.Construction.Part.MakePartHeaders import MakePartHeaders
from convert.adapters.solidworks.Archive.Definition.Construction.MakePartDef import MakePartDef
from convert.adapters.solidworks.Archive.Definition.WriteModelDef import WriteModelDef
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.History.WriteHistMut import WriteHistMut
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt, ReadNodeName
from convert.adapters.solidworks.Container.Container import BuildSldprt
from convert.adapters.solidworks.Container.Format import KResolvedFeaturesStream, KeywordsStream

from MakeRevolveGraph01 import make_profile, make_feature
from ReadRevolveInput01 import read_plan, require


@dataclass(frozen=True)
class RevolveCandidate:
    SystemValue: object
    ProfileValue: object
    FeatureValue: object
    AxisReference: object
    EndValue: object
    AngleValue: object
    HeadersValue: tuple
    DefinitionValue: object
    ConfigValue: object
    ResolvedValue: object
    StreamsValue: dict
    BytesValue: bytes
    PlanValue: object


def make_keywords(system, features, settings, plan):
    configs = tuple(KeywordConfig(FieldInt(node.FieldsValue, 'f08'), ReadNodeName(node), '')
        for node in system.ConfigValues)
    rows = tuple(KeywordFeature(FieldInt(node.FieldsValue, 'f08'), ReadNodeName(node),
        node.ClassValue.NameValue, 'Feature', (), (), None, None) for node in features[:-2])
    profile, feature = features[-2:]
    rows += (KeywordFeature(FieldInt(profile.FieldsValue, 'f08'), ReadNodeName(profile),
        None, 'Sketch', (), (), True, None), KeywordFeature(FieldInt(feature.FieldsValue, 'f08'),
        ReadNodeName(feature), 'Revolve', 'Feature', (KeywordDim('D1', degrees(plan.AngleValue), 'degree'),),
        (), None, None))
    return MakeKeywords(plan.NameValue, settings.HeaderValue.ModifiedAt, configs, rows)


def make_candidate(document, settings):
    plan = read_plan(document)
    CheckPartInput(document, settings, plan)
    require(settings.PropertiesValue is None, 'revolve prototype does not admit optional property owners')
    require(settings.DocumentUnits.AngleUnit == 'degree', 'revolve prototype requires explicit degree presentation')
    allocator = PersistentIds()
    system = MakePartBaseMut(settings, plan, allocator)
    profile, axis = make_profile(system, settings, plan, allocator)
    feature, reference, end, angle = make_feature(system, profile, axis, settings, plan, allocator)
    SetCfgStampMut(system.ConfigValues[0], allocator)
    headers = MakePartHeaders(system, settings, allocator)
    definition = MakePartDef(settings.DefinitionValue, settings.DensityValue)
    features = (*system.FeatureValues, profile.ProfileValue, feature)
    config_bytes, config = WriteConfigMut(system.RootValue, 19000, headers[0])
    context = {'model_compressed_stream': 1, 'model_is_part': 1,
        'cmgr_f658': system.ManagerValue.FieldsValue['f658']}
    resolved_bytes, resolved = WriteResolMut(features, None, 19000, config.MapValue, context)
    streams = {'Header2': WriteHeadGraph(headers[1], 19000),
        'Contents/Config-0-ModelHeader': WriteHeadGraph(headers[0], 19000),
        'Contents/Config-0': config_bytes, 'Contents/CMgr': WriteCmgrMut(system.ManagerValue, 19000),
        'Contents/CMgrHdr2': WriteMgrHeader(headers[2], 19000)[0],
        KResolvedFeaturesStream: resolved_bytes,
        'Contents/Definition': WriteModelDef(definition).OutputValue,
        '_MO_VERSION_19000/Biography': WriteHistMut(MakeBiography(), 19000)[0],
        '_MO_VERSION_19000/History': WriteHistMut(MakeFreshHist(settings.HistoryValue), 19000)[0],
        KeywordsStream: make_keywords(system, features, settings, plan)}
    return RevolveCandidate(system, profile, feature, reference, end, angle, headers,
        definition, config, resolved, streams, BuildSldprt(streams, FormatVersion=4), plan)
