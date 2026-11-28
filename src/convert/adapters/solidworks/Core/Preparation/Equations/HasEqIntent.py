from interchange.document.Models.DocumentModel import CadDocument


# a live local expression selects its owned planner before ordinary geometry only construction
def HasEqIntent(DocumentValue: CadDocument) -> bool:
    return any(
        ParamValue.expression is not None for ParamValue in DocumentValue.parameters
    )
