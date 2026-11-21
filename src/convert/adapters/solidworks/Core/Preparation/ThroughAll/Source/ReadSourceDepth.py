from convert.adapters.solidworks.Core.Preparation.ThroughAll.Source.ReadSourceEnd import (
    ReadSourceEnd,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadLength import (
    ReadLength,
)
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureStep import FeatureStep
from interchange.Records.RecordParameter import Parameter


# the total stock depth must come from its actual driving parameter rather than a synthetic cut distance
def ReadSourceDepth(DocumentValue: CadDocument, StockValue: FeatureStep) -> Parameter:
    if len(DocumentValue.parameters) != 1:
        raise ValueError("source stock has unrepresented parameter owners")
    Driver = DocumentValue.parameters[0]
    if (
        Driver.owner_id != StockValue.id
        or Driver.name != "D1"
        or Driver.role != "driving"
        or Driver.expression is not None
        or Driver.value.kind != "length"
        or Driver.value.unit != DocumentValue.units
        or StockValue.parameter_ids != (Driver.id,)
        or ReadSourceEnd(StockValue).length != Driver.value
    ):
        raise ValueError("source stock driver is stale or has unrepresented intent")
    _ = ReadLength(Driver.value)
    return Driver
