from dataclasses import replace
from types import MappingProxyType

from ansi_pair.Compose import child_mut, drawing_mut
from ansi_normalization.Rules import initialize_model
from SpatialTextMut import require
from convert.adapters.solidworks.Archive.Construction.Part.EmitPartStreams import (
    EmitPartStreams,
)
from convert.adapters.solidworks.Container.Container import BuildSldprt
from convert.adapters.solidworks.Drawing.Definition.Named.WriteNamedDef import (
    WriteNamedDef,
)


def compose_child(child, settings, keys, mode, initialization):
    child = child_mut(child, settings, keys, mode)
    require(initialization in ("fresh", "document-units"), "unknown initialization")
    if initialization == "fresh":
        return child
    initialize_model(child.SystemValue.RootValue, settings.DocumentUnits)
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


def compose_drawing(pair, inputs, mode, initialization):
    pair = drawing_mut(pair, inputs, mode)
    require(initialization in ("fresh", "document-units"), "unknown initialization")
    if initialization == "fresh":
        return pair
    initialize_model(pair.ModelGraph.ModelValue, inputs.OptionsValue.UnitValue)
    streams = dict(pair.StreamsValue)
    streams["Contents/Definition"] = WriteNamedDef(pair.UiGraph).OutputValue
    return replace(
        pair, StreamsValue=MappingProxyType(streams), BytesValue=BuildSldprt(streams)
    )
