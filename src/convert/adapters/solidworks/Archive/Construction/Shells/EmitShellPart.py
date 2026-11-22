from dataclasses import replace as ReplaceValue

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
from convert.adapters.solidworks.Archive.Construction.Shells.MakeShellMut import (
    MakeShellMut,
)
from convert.adapters.solidworks.Archive.Construction.Shells.OpenShellPlan import (
    OpenShellPlan,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadNodeName,
)
from convert.adapters.solidworks.Container.Container import BuildSldprt
from interchange.document.Models.DocumentModel import CadDocument


# shell keywords refer to the same live driver and persistent shell feature as the resolved graph
def MakeShellKey(Feature: ArchiveNode, Driver: DimensionGraph) -> KeywordFeature:
    Parameter = Driver.ParameterValue
    Thickness = RequireScalar(Parameter.FieldsValue["f58"])
    return KeywordFeature(
        FieldInt(Feature.FieldsValue, "f08"),
        ReadNodeName(Feature),
        "Shell",
        "Feature",
        (KeywordDim(ReadNodeName(Parameter), Thickness * 1000, None),),
        (),
        None,
        None,
    )


# a complete shell archive uses the ordinary part stream writers with the additional related feature
def EmitShellPart(
    DocumentValue: CadDocument, PlanValue: OpenShellPlan, Settings: PartBuildInput
) -> PartCandidate:
    Stock = PlanValue.StockValue
    CheckPartInput(DocumentValue, Settings, Stock, (PlanValue.FeatureName,))
    Candidate = MakeBlindByPlan(DocumentValue, Settings, Stock)
    Feature, Driver = MakeShellMut(Candidate, PlanValue, Settings)
    Manager = MakeMgrHeader(
        Candidate.SystemValue.ManagerValue, Settings.OutputValue.SavedAt
    )
    Roots = tuple(
        ArchiveNode.RequireNode(Value) for Value in Candidate.ResolvedValue.RootsValue
    )
    Keywords = MakePartKeys(
        Candidate.SystemValue,
        Roots,
        Settings,
        Stock,
        AdditionalRows=(MakeShellKey(Feature, Driver),),
    )
    Streams, Config, Resolved = EmitPartArchive(
        Candidate.SystemValue,
        (*Roots, Feature),
        (Candidate.HeaderValue, Candidate.TopHeader, Manager),
        Candidate.DefinitionValue,
        Settings,
        Keywords,
        BodyMapFields={"n": 0, "fcd8": []},
        WriteShell=True,
    )
    return ReplaceValue(
        Candidate,
        ManagerHeader=Manager,
        ConfigValue=Config,
        ResolvedValue=Resolved,
        StreamsValue=Streams,
        BytesValue=BuildSldprt(Streams, FormatVersion=4),
    )
