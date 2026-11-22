from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import BooleanOp
from interchange.geometry.Models.Selection import SelectPathElem
from interchange.Records.RecordTopology import TopologyCounts


# the native scope requires the same earlier stock in the dependency selection path and final body history
def ReadStockIndex(DocumentValue: CadDocument) -> int:
    First, Second, CutStep = DocumentValue.feature_timeline
    Stocks = (First.id, Second.id)
    if (
        (First.operation, Second.operation, CutStep.operation)
        != (BooleanOp.KCreate, BooleanOp.KCreate, BooleanOp.KCutOperation)
        or (First.order, Second.order, CutStep.order) != (0, 1, 2)
        or First.input_feature_ids
        or Second.input_feature_ids
        or len(CutStep.input_feature_ids) != 1
        or CutStep.input_feature_ids[0] not in Stocks
        or len(CutStep.selection_ids) != 2
    ):
        raise ValueError("selected revolve cut needs one actual prior stock")
    StockId = CutStep.input_feature_ids[0]
    Chosen = Stocks.index(StockId)
    Picks = {Value.id: Value for Value in DocumentValue.selections}
    StockPick = Picks.get(CutStep.selection_ids[1])
    if (
        StockPick is None
        or StockPick.name != "Selected historical stock"
        or StockPick.path != (SelectPathElem("feature", StockId, "body"),)
        or StockPick.query
        or StockPick.point is not None
        or StockPick.provenance is not None
        or StockPick.attributes
    ):
        raise ValueError("selected revolve body reference differs from its dependency")
    Untouched, Result = DocumentValue.bodies
    Stock = (First, Second)[1 - Chosen]
    if (
        Untouched.final_feature_id,
        Untouched.name,
        Result.final_feature_id,
        Result.name,
    ) != (
        Stock.id,
        Stock.name,
        CutStep.id,
        CutStep.name,
    ) or any(
        Value.topology != TopologyCounts()
        or Value.provenance is not None
        or Value.material_id is not None
        or Value.attributes
        for Value in DocumentValue.bodies
    ):
        raise ValueError("selected revolve cut needs its two named final body owners")
    return Chosen
