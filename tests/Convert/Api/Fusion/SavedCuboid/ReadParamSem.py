from interchange import CadDocument
from interchange.Records.RecordParameter import ParameterValue


# parameter references compare by named roles because native object ids are allocated independently
def ReadParamSem(
    Document: CadDocument,
) -> tuple[tuple[str, ParameterValue, str, str, str, tuple[str, ...]], ...]:
    Features = {Feature.id: Feature.name for Feature in Document.feature_timeline}
    Names = {Param.id: Param.name for Param in Document.parameters}
    return tuple(
        (
            Param.name,
            Param.value,
            Param.role.value,
            Features[Param.owner_id] if Param.owner_id else "",
            Param.expression.source if Param.expression is not None else "",
            (
                tuple(Names[Owner] for Owner in Param.expression.parameter_ids)
                if Param.expression is not None
                else ()
            ),
        )
        for Param in Document.parameters
    )
