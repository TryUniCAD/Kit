from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordDim import (
    KeywordDim,
)
from convert.adapters.solidworks.Archive.Construction.Part.EmitPartArchive import (
    EmitPartArchive,
)
from convert.adapters.solidworks.Archive.Construction.Part.MakePartKeys import (
    MakePartKeys,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Construction.Datums.PrincipalAxes.AxisKeyRow import (
    AxisKeyRow,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Container.Container import BuildSldprt


# the complete cache free part must keep its actual stock and append the registered axis roots
def EmitAxesPart(
    StockValue: PartCandidate,
    InputValue: PartBuildInput,
    SketchDims: tuple[KeywordDim, ...],
    AxisNodes: tuple[ArchiveNode, ...],
    Headers: tuple[ArchiveNode, ArchiveNode, ArchiveNode],
) -> PartCandidate:
    SystemValue = StockValue.SystemValue
    StockRoots = (
        *SystemValue.FeatureValues,
        StockValue.ProfileValue.ProfileValue,
        StockValue.BossValue.FeatureValue,
    )
    if StockValue.ResolvedValue.RootsValue != StockRoots:
        raise ValueError(
            "principal axes require the complete actual anchored stock history"
        )
    KeysValue = MakePartKeys(
        SystemValue,
        StockRoots,
        InputValue,
        StockValue.PlanValue,
        SketchDims,
        AdditionalRows=tuple(AxisKeyRow(Value) for Value in AxisNodes),
    )
    Streams, ConfigValue, ResolvedValue = EmitPartArchive(
        SystemValue,
        (*StockRoots, *AxisNodes),
        Headers,
        StockValue.DefinitionValue,
        InputValue,
        KeysValue,
    )
    if any(
        "Partition" in NameValue or "LocalBodies" in NameValue for NameValue in Streams
    ):
        raise ValueError("generated principal axes require a cache-free stock part")
    return ReplaceValue(
        StockValue,
        HeaderValue=Headers[0],
        TopHeader=Headers[1],
        ManagerHeader=Headers[2],
        StreamsValue=Streams,
        ConfigValue=ConfigValue,
        ResolvedValue=ResolvedValue,
        BytesValue=BuildSldprt(Streams, FormatVersion=4),
    )
