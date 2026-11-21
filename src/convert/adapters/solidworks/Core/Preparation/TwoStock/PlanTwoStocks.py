from convert.adapters.solidworks.Core.Preparation.TwoStock.CheckStockPick import (
    CheckStockPick,
)
from convert.adapters.solidworks.Core.Preparation.TwoStock.CheckStockScope import (
    CheckStockScope,
)
from convert.adapters.solidworks.Core.Preparation.TwoStock.CheckStockShape import (
    CheckStockShape,
)
from convert.adapters.solidworks.Core.Preparation.TwoStock.ReadStockCircle import (
    ReadStockCircle,
)
from convert.adapters.solidworks.Core.Preparation.TwoStock.ReadStockInput import (
    ReadStockInput,
)
from convert.adapters.solidworks.Core.Preparation.TwoStock.ReadStockName import (
    ReadStockName,
)
from convert.adapters.solidworks.Core.Preparation.TwoStock.ReadStockRows import (
    ReadStockRows,
)
from convert.adapters.solidworks.Core.Preparation.TwoStock.TwoStockPlan import (
    TwoStockPlan,
)
from interchange.document.Models.DocumentModel import CadDocument


# eligibility and preparation must use one exact lossless projection of the bounded neutral feature intent
def PlanTwoStocks(DocumentValue: CadDocument) -> TwoStockPlan:
    CheckStockScope(DocumentValue)
    NameValue = ReadStockName(DocumentValue)
    FrontStock, RightStock, CutValue = DocumentValue.feature_timeline
    FrontDraw, RightDraw, CutDraw = ReadStockRows(DocumentValue)
    Planes = {Value.id: Value for Value in DocumentValue.support_planes}
    Drivers = {Value.id: Value for Value in DocumentValue.parameters}
    if any(len(Value.parameter_ids) != 1 for Value in (FrontStock, RightStock)) or {
        *FrontStock.parameter_ids,
        *RightStock.parameter_ids,
    } != set(Drivers):
        raise ValueError("the two independent stocks require distinct actual D1 owners")
    Untouched, ResultBody = DocumentValue.bodies
    if any(
        Value.final_feature_id != OwnerValue.id
        or Value.name != OwnerValue.name
        or Value.material_id is not None
        or Value.attributes
        for Value, OwnerValue in ((Untouched, RightStock), (ResultBody, CutValue))
    ):
        raise ValueError(
            "two-stock bodies require their ordered producers and implicit labels"
        )
    CheckStockPick(FrontStock, CutValue, DocumentValue.selections[0])
    FrontPlan = ReadStockInput(
        NameValue,
        FrontStock,
        FrontDraw,
        Planes[FrontDraw.support_plane_id],
        Drivers[FrontStock.parameter_ids[0]],
        "z",
        f"{FrontStock.id}:historical-stock",
    )
    RightPlan = ReadStockInput(
        NameValue,
        RightStock,
        RightDraw,
        Planes[RightDraw.support_plane_id],
        Drivers[RightStock.parameter_ids[0]],
        "x",
        Untouched.id,
    )
    PlanValue = TwoStockPlan(
        (FrontPlan, RightPlan),
        ReadStockCircle(CutDraw),
        CutDraw.name,
        CutValue.name,
        ResultBody.id,
    )
    CheckStockShape(PlanValue)
    return PlanValue
