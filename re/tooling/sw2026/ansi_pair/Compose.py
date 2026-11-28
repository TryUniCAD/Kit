from collections.abc import Mapping
from dataclasses import replace
from types import MappingProxyType

from SpatialTextMut import concrete, require
from convert.adapters.solidworks.Archive.Construction.Part.EmitPartStreams import (
    EmitPartStreams,
)
from convert.adapters.solidworks.Archive.Construction.Styles.Ansi.MakeAnsiDetails import (
    MakeAnsiDetails,
)
from convert.adapters.solidworks.Container.Container import BuildSldprt
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Drawing.Definition.Named.WriteNamedDef import (
    WriteNamedDef,
)


def standard_mut(root, mode):
    actual = concrete(root.FieldsValue["fba8"], "moISO_c")
    require(not actual.FieldsValue, "fresh UI standard has an unexpected body")
    if mode == "ansi":
        root.FieldsValue["fba8"] = ArchiveNode(RuntimeClass("moANSI_c", 1), {})


def child_mut(child, settings, keys, mode):
    require(mode in ("iso", "ansi"), "unknown full-pair detail mode")
    wanted = "moANSI_c" if mode == "ansi" else "moISO_c"
    standard_mut(child.DefinitionValue.DocumentValue, mode)
    standard = concrete(child.DefinitionValue.DocumentValue.FieldsValue["fba8"], wanted)
    require(not standard.FieldsValue, "UI standard has an unexpected body")
    if mode == "iso":
        require(
            child.SystemValue.RootValue.FieldsValue["fae0"]["f10"] == 1,
            "ISO control has another actual detail selector",
        )
        return child
    style = replace(settings.StyleValue, StandardValue=0)
    child.SystemValue.RootValue.FieldsValue["fae0"] = MakeAnsiDetails(style)
    settings = replace(settings, StyleValue=style)
    streams, config, resolved = EmitPartStreams(
        child.SystemValue,
        child.ResolvedValue.RootsValue,
        (child.HeaderValue, child.TopHeader, child.ManagerHeader),
        child.DefinitionValue,
        settings,
        child.PlanValue,
        keys,
    )
    return replace(
        child,
        ConfigValue=config,
        ResolvedValue=resolved,
        StreamsValue=MappingProxyType(streams),
        BytesValue=BuildSldprt(streams),
    )


def drawing_mut(pair, inputs, mode):
    wanted = "moANSI_c" if mode == "ansi" else "moISO_c"
    standard_mut(pair.UiGraph.DocumentValue, mode)
    standard = concrete(pair.UiGraph.DocumentValue.FieldsValue["fba8"], wanted)
    require(not standard.FieldsValue, "drawing UI standard has an unexpected body")
    model = concrete(pair.UiGraph.DocumentValue.FieldsValue["model"], "moDrawing_c")
    require(
        model is pair.ModelGraph.ModelValue, "drawing model ownership aliases differ"
    )
    if mode == "iso":
        require(
            model.FieldsValue["fae0"]["f10"] == 1,
            "ISO drawing control has another actual detail selector",
        )
        return pair
    style = replace(inputs.OptionsValue.StyleValue, StandardValue=0)
    model.FieldsValue["fae0"] = MakeAnsiDetails(style)
    streams = dict(pair.StreamsValue)
    streams["Contents/Definition"] = WriteNamedDef(pair.UiGraph).OutputValue
    return replace(
        pair, StreamsValue=MappingProxyType(streams), BytesValue=BuildSldprt(streams)
    )
