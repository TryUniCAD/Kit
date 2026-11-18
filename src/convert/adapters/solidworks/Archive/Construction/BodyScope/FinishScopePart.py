from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Construction.Part.EmitPartStreams import (
    EmitPartStreams,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Container.Container import BuildSldprt


# ownership changes require every stream to be emitted from the actual shared graph and its updated archive map
def FinishScopePart(
    CandidateValue: PartCandidate, InputValue: PartBuildInput
) -> PartCandidate:
    FeatureValues = tuple(
        ArchiveNode.RequireNode(FeatureValue)
        for FeatureValue in CandidateValue.ResolvedValue.RootsValue
    )
    StreamsValue, ConfigValue, ResolvedValue = EmitPartStreams(
        CandidateValue.SystemValue,
        FeatureValues,
        (
            CandidateValue.HeaderValue,
            CandidateValue.TopHeader,
            CandidateValue.ManagerHeader,
        ),
        CandidateValue.DefinitionValue,
        InputValue,
        CandidateValue.PlanValue,
        CutValue=CandidateValue.CutValue,
    )
    if any("Partition" in NameValue for NameValue in StreamsValue):
        raise ValueError("cold selected stock must not transmit kernel body data")
    return ReplaceValue(
        CandidateValue,
        StreamsValue=StreamsValue,
        ConfigValue=ConfigValue,
        ResolvedValue=ResolvedValue,
        BytesValue=BuildSldprt(StreamsValue, FormatVersion=4),
    )
