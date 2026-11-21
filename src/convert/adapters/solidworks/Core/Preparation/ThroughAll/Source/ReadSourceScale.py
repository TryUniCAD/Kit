from interchange.document.Models.DocumentModel import CadDocument


# source geometry must convert through explicit modeled units without interpreting native cached scalar bags
def ReadSourceScale(DocumentValue: CadDocument) -> float:
    ScalesValue = {"mm": 0.001, "m": 1.0, "in": 0.0254}
    if DocumentValue.units not in ScalesValue:
        raise ValueError(
            "source owner projection requires explicit supported length units"
        )
    return ScalesValue[DocumentValue.units]
