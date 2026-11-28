from convert.adapters.solidworks.Core.TypedResolved.Fillets.FilletHistory import (
    FilletHistory,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import FeatureKind
from interchange.Features.FeatureExtrude import ExtrudeFeature
from interchange.Features.FeatureKinds import FilletFeature
from interchange.Features.FeatureStep import FeatureStep


# the actual resolved stock and fillet must both be present in the public history
def ReadFilletStep(
    Document: CadDocument,
    History: FilletHistory,
) -> tuple[FeatureStep, FeatureStep]:
    Features = {Value.id: Value for Value in Document.feature_timeline}
    Owners = History.OwnersValue
    StockValue, StepValue = (
        Features[f"sldprt:feature:{NativeNodeId(Value)}"]
        for Value in (Owners.StockValue, Owners.FilletValue)
    )
    if (
        StockValue.kind != FeatureKind.KExtrusion
        or not isinstance(StockValue.definition, ExtrudeFeature)
        or StockValue.suppressed
        or StepValue.suppressed
        or StepValue.kind != FeatureKind.KFillet
        or not isinstance(StepValue.definition, FilletFeature)
        or StepValue.definition.variable_radius_parameter_ids
        or StockValue.order >= StepValue.order
        or StepValue.name != ReadNativeName(Owners.FilletValue)
        or StockValue.name != ReadNativeName(Owners.StockValue)
        or StepValue.input_feature_ids != (StockValue.id,)
    ):
        raise ValueError(
            "saved fillet does not retain its actual preceding public stock"
        )
    return StockValue, StepValue
