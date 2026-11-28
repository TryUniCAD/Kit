from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.CheckSeedInput import (
    CheckSeedInput,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.SeedStockInput import (
    SeedStockInput,
)
from convert.adapters.solidworks.Core.Preparation.DefaultPartTree import (
    DefaultPartTree,
)


# independent authored feature names must survive the common native tree initialization
def CheckPatNames(StockValue: SeedStockInput, *LaterNames: str) -> None:
    StockNames = CheckSeedInput(StockValue)
    SystemValue = DefaultPartTree("Front Plane", StockValue.SavedAt)
    NamesValue = (
        SystemValue.CabinetName,
        SystemValue.OriginName,
        *(Label for _, Label in (*SystemValue.FolderValues, *SystemValue.PlaneNames)),
        *StockNames,
        *LaterNames,
    )
    if any(
        type(Label) is not str or not Label or not Label.isprintable()
        for Label in LaterNames
    ) or len(set(NamesValue)) != len(NamesValue):
        raise ValueError(
            "pattern feature hinge and plane labels must be distinct actual native names"
        )
