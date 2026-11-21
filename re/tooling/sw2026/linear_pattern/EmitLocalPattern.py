from dataclasses import replace
from math import degrees
from xml.etree.ElementTree import Element, SubElement

from convert.adapters.solidworks.Archive.Construction.Metadata.FrameKeywords import FrameKeywords
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordDim import KeywordDim
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeKeyDimMut import MakeKeyDimMut
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeKeyFeatMut import MakeKeyFeatMut
from convert.adapters.solidworks.Archive.Construction.Part.EmitPartArchive import EmitPartArchive
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakeSketchKeys import MakeSketchKeys
from convert.adapters.solidworks.Archive.Definition.Construction.MakePartDef import MakePartDef
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt, ReadNodeName
from convert.adapters.solidworks.Container.Container import BuildSldprt
from convert.adapters.solidworks.Core.Preparation.TwoStock.StockKeywords import StockKeyRow

from CheckPatternAngleOwners import require
from MakeLocalPattern import make_pattern


def make_keywords(graph):
    seed = graph.seed
    root = seed.system.RootValue
    config, = seed.system.ConfigValues
    model = Element("Keywords", {"id": str(seed.settings.HeaderValue.ModifiedAt), "Name": ReadNodeName(root)})
    SubElement(model, "Configuration", {"id": str(FieldInt(config.FieldsValue, "f08")), "Name": ReadNodeName(config),
                                       "Type": "ConfigurationManager"})
    unit = seed.settings.DocumentUnits.LengthUnit
    words = tuple(StockKeyRow(node, "Feature") for node in seed.system.FeatureValues)
    for operation in (seed.plate, seed.seed):
        profile = operation.ProfileValue.ProfileValue
        words += (StockKeyRow(profile, "Sketch"), StockKeyRow(operation.FeatureValue, "Extrusion",
                  MakeSketchKeys((operation.DriverValue,), unit), (profile.FieldsValue["f08"],)))
    angle = graph.plane_driver.ParameterValue
    require(angle.ClassValue.NameValue == "moAngleParameter_c" and ReadNodeName(angle) == "D1",
            "pattern Keywords need the actual local plane angle")
    count, pitch, *_ = graph.pattern_drivers
    require(type(count.ParameterValue.FieldsValue["f58"]) is int and ReadNodeName(count.ParameterValue) == "D1"
            and ReadNodeName(pitch.ParameterValue) == "D3", "pattern Keywords require the actual live count and pitch")
    words += (
        StockKeyRow(graph.axis, "Feature"),
        StockKeyRow(graph.plane, "Feature"),
        StockKeyRow(graph.pattern, "Feature", (KeywordDim("D1", count.ParameterValue.FieldsValue["f58"], None),
                                               *MakeSketchKeys((pitch,), unit))),
    )
    vocabulary = {"moRefAxis_c": "Axis", "moRefPlane_c": "Plane", "moLPattern_c": "LPattern"}
    for row in sorted(words, key=lambda value: (value.TagValue, str(value.IdValue))):
        MakeKeyFeatMut(model, replace(row, KindValue=vocabulary.get(row.KindValue, row.KindValue)))
        if row.IdValue == graph.plane.FieldsValue["f08"]:
            MakeKeyDimMut(model[-1], KeywordDim("D1", degrees(angle.FieldsValue["f58"]), "degree"))
    return FrameKeywords(model, True)


def emit_pattern(seed_intent, axis_name, plane_intent, annotation, pattern_intent):
    graph = make_pattern(seed_intent, axis_name, plane_intent, annotation, pattern_intent)
    seed = graph.seed
    definition = MakePartDef(seed.settings.DefinitionValue, seed.settings.DensityValue)
    streams, config, resolved = EmitPartArchive(seed.system, graph.roots, graph.headers, definition, seed.settings, make_keywords(graph))
    require(config.MapValue.CounterValue < resolved.MapValue.CounterValue and resolved.RootsValue == graph.roots
            and resolved.RootsValue[:len(seed.roots)] == seed.roots
            and all("Partition" not in name and "LocalBodies" not in name for name in streams),
            "local pattern constructor must extend the same ordinary part and omit stored physical body rows")
    container = BuildSldprt(streams, FormatVersion=4)
    return graph, streams, container
