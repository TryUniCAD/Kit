from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import BooleanOp
from interchange.geometry.Models.Selection import SelectPathElem
from interchange.Records.RecordTopology import TopologyCounts


# the native scope requires the same unique earlier stock in the dependency, selection path and final body history
def ReadSelectedStock(DocumentValue: CadDocument) -> int:
    First, Second, Cut = DocumentValue.feature_timeline
    Stocks = (First.id, Second.id)
    if (
        (First.operation, Second.operation, Cut.operation)
        != (BooleanOp.KCreate, BooleanOp.KCreate, BooleanOp.KCutOperation)
        or (First.order, Second.order, Cut.order) != (0, 1, 2)
        or First.input_feature_ids
        or Second.input_feature_ids
        or len(Cut.input_feature_ids) != 1
        or Cut.input_feature_ids[0] not in Stocks
        or len(Cut.selection_ids) != 2
    ):
        raise ValueError("selected revolve cut needs one actual prior stock")
    StockId = Cut.input_feature_ids[0]
    Chosen = Stocks.index(StockId)
    Picks = {Value.id: Value for Value in DocumentValue.selections}
    Pick = Picks.get(Cut.selection_ids[1])
    if (
        Pick is None
        or Pick.name != "Selected historical stock"
        or Pick.path != (SelectPathElem("feature", StockId, "body"),)
        or Pick.query
        or Pick.point is not None
        or Pick.provenance is not None
        or Pick.attributes
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
        Cut.id,
        Cut.name,
    ) or any(
        Value.topology != TopologyCounts()
        or Value.provenance is not None
        or Value.material_id is not None
        or Value.attributes
        for Value in DocumentValue.bodies
    ):
        raise ValueError("selected revolve cut needs its two named final body owners")
    return Chosen
