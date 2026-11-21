from interchange.document.Models.DocumentModel import CadDocument


# each driven owner belongs to the ordered source history without extra provenance or state
def CheckPatHistory(DocumentValue: CadDocument) -> None:
    StepsValue = DocumentValue.feature_timeline
    if any(
        StepValue.provenance is not None
        or StepValue.attributes
        or StepValue.suppressed
        or StepValue.configuration_states
        for StepValue in StepsValue
    ):
        raise ValueError("neutral timeline contains extra feature state")
    if any(
        Before.order >= After.order
        for Before, After in zip(StepsValue[:-1], StepsValue[1:], strict=True)
    ):
        raise ValueError(
            "neutral operation order must retain the two stocks followed by their datum and pattern"
        )
    RecordsValue = (
        *((Value.attributes, Value.provenance) for Value in DocumentValue.parameters),
        *(
            (Value.attributes, Value.provenance)
            for Value in DocumentValue.support_planes
        ),
        *((Value.attributes, Value.provenance) for Value in DocumentValue.sketches),
        *((Value.attributes, Value.provenance) for Value in DocumentValue.bodies),
        *(
            (Entity.attributes, Entity.provenance)
            for SketchValue in DocumentValue.sketches
            for Entity in SketchValue.entities
        ),
    )
    if any(
        Attributes or Provenance is not None for Attributes, Provenance in RecordsValue
    ):
        raise ValueError("unrepresented provenance or extension in neutral part")
    ParamIds = tuple(
        Identity for StepValue in StepsValue for Identity in StepValue.parameter_ids
    )
    ChoiceIds = tuple(
        Identity for StepValue in StepsValue for Identity in StepValue.selection_ids
    )
    if (
        len(ParamIds) != len(set(ParamIds))
        or set(ParamIds) != {Value.id for Value in DocumentValue.parameters}
        or len(ChoiceIds) != len(set(ChoiceIds))
        or set(ChoiceIds) != {Value.id for Value in DocumentValue.selections}
    ):
        raise ValueError(
            "neutral features must individually own every distinct parameter and selection"
        )
