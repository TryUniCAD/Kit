from convert.adapters.solidworks.Archive.Construction.Part.Neutral.BlindPlan import (
    BlindPlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadLength import (
    ReadLength,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadRectParams import (
    ReadRectParams,
)
from interchange.document.Models.DocumentModel import CadDocument


# the signed stock geometry and every emitted driver must use the same modeled value
def CheckAxisStock(DocumentValue: CadDocument, PlanValue: BlindPlan) -> None:
    if (
        DocumentValue.brep is not None
        or DocumentValue.brep_payloads
        or DocumentValue.units != "mm"
        or DocumentValue.bodies[0].name == PlanValue.FeatureName
    ):
        raise ValueError(
            "attached axes need a clean signed part with an authored stock label"
        )
    Params = ReadRectParams(DocumentValue)
    Lengths = (PlanValue.WidthValue, PlanValue.HeightValue, PlanValue.DepthValue)
    if any(
        ReadLength(Driver.value) != LengthValue
        for Driver, LengthValue in zip(Params, Lengths, strict=True)
    ):
        raise ValueError("attached axis stock requires exact live driver distances")
