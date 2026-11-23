from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordDim import (
    KeywordDim,
)
from convert.adapters.solidworks.Archive.Construction.Part.EmitPartStreams import (
    EmitPartStreams,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import RequireNode
from convert.adapters.solidworks.Container.Container import BuildSldprt


# the complete original generated graph must supply every stream again after real output ownership changes its archive map
def FinishNamedPart(
    CandidateValue: PartCandidate,
    InputValue: PartBuildInput,
    SketchDims: tuple[KeywordDim, ...],
    *,
    PartRelations: bool = False,
) -> PartCandidate:
    if PartRelations:
        RootValue = CandidateValue.SystemValue.RootValue
        Fields = RequireNode(RootValue.FieldsValue["f9d0"], "moRelMgr_c").FieldsValue
        if Fields["owner"] is not RootValue or Fields["f150"] != 1:
            raise ValueError(
                "named body with an equation requires its actual relation owner"
            )
    StreamsValue, ConfigValue, ResolvedValue = EmitPartStreams(
        CandidateValue.SystemValue,
        (
            *CandidateValue.SystemValue.FeatureValues,
            CandidateValue.ProfileValue.ProfileValue,
            CandidateValue.BossValue.FeatureValue,
        ),
        (
            CandidateValue.HeaderValue,
            CandidateValue.TopHeader,
            CandidateValue.ManagerHeader,
        ),
        CandidateValue.DefinitionValue,
        InputValue,
        CandidateValue.PlanValue,
        SketchDims,
        PartRelations=PartRelations,
    )
    if any("Partition" in NameValue for NameValue in StreamsValue):
        raise ValueError("cold named part must not transmit a native geometry cache")
    return ReplaceValue(
        CandidateValue,
        StreamsValue=StreamsValue,
        ConfigValue=ConfigValue,
        ResolvedValue=ResolvedValue,
        BytesValue=BuildSldprt(StreamsValue, FormatVersion=4),
    )
