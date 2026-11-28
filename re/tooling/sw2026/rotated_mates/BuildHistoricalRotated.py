from dataclasses import replace

from ProjectRotatedModel import literal_recipes
from convert.adapters.solidworks.Archive.Construction.Assembly.EmitAsmStreams import EmitAsmStreams
from convert.adapters.solidworks.Archive.Construction.Assembly.Headers.MakeAsmHeaders import MakeAsmHeaders
from convert.adapters.solidworks.Archive.Construction.Assembly.MakeAsmBase import MakeAsmBase
from convert.adapters.solidworks.Archive.Construction.Assembly.Occurrences.PutPartRefsMut import PutPartRefsMut
from convert.adapters.solidworks.Archive.Construction.AssemblyGroups.CheckGroupIn import CheckGroupIn
from convert.adapters.solidworks.Archive.Construction.AssemblyGroups.MakeGroupMut import MakeGroupMut
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordConfig import KeywordConfig
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordDim import KeywordDim
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordFeature import KeywordFeature
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeKeywords import MakeKeywords
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import PersistentIds
from convert.adapters.solidworks.Archive.Construction.Part.CheckPartInput import CheckPartInput
from convert.adapters.solidworks.Archive.Construction.Part.FinishBlindMut import FinishBlindMut
from convert.adapters.solidworks.Archive.Construction.Part.MakePartBaseMut import MakePartBaseMut
from convert.adapters.solidworks.Archive.Construction.Part.MakePartProfMut import MakePartProfMut
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectRectDims import ProjectRectDims
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakeRectDimsMut import MakeRectDimsMut
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakeSketchKeys import MakeSketchKeys
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt, ReadNodeName
from convert.adapters.solidworks.Container.Container import BuildSldprt


HEADER = "Header2"
BIOGRAPHY = "_MO_VERSION_19000/Biography"
HISTORY = "_MO_VERSION_19000/History"
MODEL_HEADER = "Contents/Config-0-ModelHeader"
CONFIG = "Contents/Config-0"
MANAGER = "Contents/CMgr"
DIRECTORY = "Contents/CMgrHdr2"
RESOLVED = "Contents/Config-0-ResolvedFeatures"
MATES = "Contents/Config-0-MatesList"
DEFINITION = "Contents/Definition"
KEYWORDS = "swXmlContents/KeyWords"
TREE = "swXmlContents/COMPINSTANCETREE"
PARENT_ORDER = (HEADER, BIOGRAPHY, HISTORY, MODEL_HEADER, CONFIG, MANAGER, RESOLVED, MATES, DEFINITION, TREE, KEYWORDS)
CHILD_ORDER = (HEADER, BIOGRAPHY, HISTORY, MODEL_HEADER, KEYWORDS, CONFIG, MANAGER, DEFINITION, RESOLVED, DIRECTORY)


def native_role(node):
    kind = node.ClassValue.NameValue
    if kind == "moRefPlane_c":
        return "Feature", "PLANE"
    if kind == "moOriginProfileFeature_c":
        return "Sketch", "Origin"
    if kind == "moProfileFeature_c":
        return "Sketch", kind
    if kind == "moExtrusion_c":
        return "Extrusion", kind
    return "Feature", kind


def historical_key(part, intent, plan, sketch_dims):
    configs = tuple(
        KeywordConfig(FieldInt(node.FieldsValue, "f08"), ReadNodeName(node), "")
        for node in part.SystemValue.ConfigValues
    )
    features = tuple(
        row for row in part.ResolvedValue.RootsValue
        if row is not None
    )
    length_unit_m = {"mm": 0.001, "m": 1.0, "in": 0.0254}[intent.DocumentUnits.LengthUnit]
    rows = []
    for node in features:
        tag, kind = native_role(node)
        if kind == "moProfileFeature_c":
            dimensions = sketch_dims
        elif tag == "Extrusion":
            dimensions = (KeywordDim("D1", plan.DepthValue / length_unit_m, None),)
        else:
            dimensions = ()
        rows.append(KeywordFeature(FieldInt(node.FieldsValue, "f08"), ReadNodeName(node),
                                   kind, tag, dimensions, (), None, None))
    return MakeKeywords(plan.NameValue, intent.HeaderValue.ModifiedAt, configs, tuple(rows))


def historical_child(document, intent, dimensions):
    plan = ProjectRectDims(document)
    CheckPartInput(document, intent, plan)
    allocator = PersistentIds()
    system = MakePartBaseMut(intent, plan, allocator)
    for owner in ("f9d8", "fa48", "fa50"):
        system.RootValue.FieldsValue[owner] = None
    profile = MakePartProfMut(system, intent, plan, allocator)
    drivers = MakeRectDimsMut(profile, dimensions, allocator, plan.SketchDriverNames)
    names = MakeSketchKeys(drivers, intent.DocumentUnits.LengthUnit)
    part = FinishBlindMut(system, profile, intent, plan, allocator, names)
    streams = {**part.StreamsValue, KEYWORDS: historical_key(part, intent, plan, names)}
    return replace(part, StreamsValue=streams,
                   BytesValue=BuildSldprt(((name, streams[name]) for name in CHILD_ORDER), FormatVersion=4))


def historical_parent(child, authored, plan, intent):
    CheckGroupIn(child, intent, plan.Occurrences, plan.MatesValue, plan.FixedIndex)
    state = MakeAsmBase(intent)
    headers = MakeAsmHeaders(state, intent)
    references = PutPartRefsMut(state, child, intent, plan.Occurrences, headers)
    mates = []
    for row, value in zip(authored, plan.MatesValue, strict=True):
        tick = row["created_at"]
        event = replace(intent.HeaderValue, CreatedAt=tick,
                        ModifiedAt=max(tick, intent.HeaderValue.ModifiedAt))
        allowed = replace(intent, HeaderValue=event)
        mates.append(MakeGroupMut(state, child, allowed, value, references, headers, tuple(mates),
                                  plan.FixedIndex))
    result = EmitAsmStreams(state, child, intent, headers, references, tuple(mates))
    streams = {name: result.StreamsValue[name] for name in PARENT_ORDER}
    return BuildSldprt(streams, FormatVersion=4), streams


def build(bundle, plan):
    parent_intent, child_intent, dimensions = literal_recipes(bundle, plan)
    child = historical_child(plan.ChildDocument, child_intent, dimensions)
    parent, streams = historical_parent(child, bundle["mates"], plan, parent_intent)
    return (parent, streams), (child.BytesValue, child.StreamsValue)
