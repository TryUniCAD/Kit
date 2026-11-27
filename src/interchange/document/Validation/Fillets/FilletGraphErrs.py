from typing import Mapping as TypeMap

from interchange.document.Models.DocumentModel import CadDocument
from interchange.document.Validation.Fillets.CheckFilletHist import CheckFilletHist
from interchange.Features.FeatureStep import FeatureStep
from interchange.Features.Fillets.RadiusFillet import RadiusFillet
from interchange.geometry.Models.Selection import Selection
from interchange.Records.RecordParameter import Parameter


# full document validation needs the selected predecessor graph in addition to scalar driver checks
def FilletGraphErrs(
    StepValue: FeatureStep,
    Document: CadDocument,
    Features: TypeMap[str, FeatureStep],
    Parameters: TypeMap[str, Parameter],
    Selections: TypeMap[str, Selection],
) -> tuple[str, ...]:
    Definition = StepValue.definition
    if not isinstance(Definition, RadiusFillet):
        return ()
    try:
        CheckFilletHist(
            StepValue, Definition, Document, Features, Parameters, Selections
        )
    except ValueError as ErrorInfo:
        return (
            f"radius fillet {StepValue.id} has invalid selected history: {ErrorInfo}",
        )
    return ()
