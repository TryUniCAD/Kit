from dataclasses import replace as ReplaceValue
from math import degrees as Degrees

from convert.adapters.solidworks.Archive.Construction.Chamfers.MakeChmfGraph import (
    MakeChmfMut,
)
from convert.adapters.solidworks.Archive.Construction.Chamfers.ChmfPlan import ChmfPlan
from convert.adapters.solidworks.Archive.Construction.Dimensions.DimensionGraph import (
    DimensionGraph,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordDim import (
    KeywordDim,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordFeature import (
    KeywordFeature,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeMgrHeader import (
    MakeMgrHeader,
)
from convert.adapters.solidworks.Archive.Construction.Part.CheckPartInput import (
    CheckPartInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.EmitPartArchive import (
    EmitPartArchive,
)
from convert.adapters.solidworks.Archive.Construction.Part.MakeBlindPart import (
    MakeBlindByPlan,
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
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadNodeName,
)
from convert.adapters.solidworks.Container.Container import BuildSldprt
from interchange.document.Models.DocumentModel import CadDocument


# the keyword index uses the actual live owner and each generated native parameter
def MakeChmfKey(
    Feature: ArchiveNode,
    Drivers: tuple[DimensionGraph, ...],
) -> KeywordFeature:
    RowsValue: list[KeywordDim] = []
    for Driver in Drivers:
        Param = Driver.ParameterValue
        Value = RequireScalar(Param.FieldsValue["f58"])
        NameValue = ReadNodeName(Param)
        if Param.ClassValue.NameValue == "moAngleParameter_c":
            RowsValue.append(KeywordDim(NameValue, Degrees(Value), "degree"))
        else:
            RowsValue.append(KeywordDim(NameValue, Value * 1000, None))
    return KeywordFeature(
        FieldInt(Feature.FieldsValue, "f08"),
        ReadNodeName(Feature),
        "Chamfer",
        "Feature",
        tuple(RowsValue),
        (),
        None,
        None,
    )


# the ordinary chamfer extends the same freshly generated stock and all complete part streams
def EmitChmfPart(
    DocumentValue: CadDocument,
    PlanValue: ChmfPlan,
    Settings: PartBuildInput,
) -> PartCandidate:
    StockPlan = PlanValue.StockValue
    CheckPartInput(DocumentValue, Settings, StockPlan, (PlanValue.FeatureName,))
    Candidate = MakeBlindByPlan(DocumentValue, Settings, StockPlan)
    Feature, Drivers = MakeChmfMut(Candidate, PlanValue, Settings)
    Manager = MakeMgrHeader(
        Candidate.SystemValue.ManagerValue, Settings.OutputValue.SavedAt
    )
    Features = Candidate.ResolvedValue.RootsValue
    if any(Value is None for Value in Features):
        raise ValueError("cold chamfer needs the complete stock root order")
    Roots = tuple(ArchiveNode.RequireNode(Value) for Value in Features)
    Keywords = MakePartKeys(
        Candidate.SystemValue,
        Roots,
        Settings,
        StockPlan,
        AdditionalRows=(MakeChmfKey(Feature, Drivers),),
    )
    Streams, Config, Resolved = EmitPartArchive(
        Candidate.SystemValue,
        (*Roots, Feature),
        (Candidate.HeaderValue, Candidate.TopHeader, Manager),
        Candidate.DefinitionValue,
        Settings,
        Keywords,
        BodyMapFields={"n": 0, "fcd8": []},
        WriteChamfers=True,
    )
    return ReplaceValue(
        Candidate,
        ManagerHeader=Manager,
        ConfigValue=Config,
        ResolvedValue=Resolved,
        StreamsValue=Streams,
        BytesValue=BuildSldprt(Streams, FormatVersion=4),
    )
