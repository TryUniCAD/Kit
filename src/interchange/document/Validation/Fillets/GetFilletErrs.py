from typing import Mapping as TypeMap

from interchange.Features.Fillets.GetFilletVals import GetFilletVals
from interchange.Features.Fillets.RadiusFillet import RadiusFillet
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.Selection import Selection
from interchange.Records.RecordParameter import Parameter


# complete document validation must reject broken selected edge and driver ownership
def GetFilletErrs(
    StepValue: FeatureStep,
    Definition: RadiusFillet,
    Parameters: TypeMap[str, Parameter],
    Selections: TypeMap[str, Selection],
) -> tuple[str, ...]:
    try:
        _ = GetFilletVals(StepValue, Definition, Parameters, Selections)
    except ValueError as ErrorInfo:
        return (f"radius fillet {StepValue.id} is invalid: {ErrorInfo}",)
    return ()
