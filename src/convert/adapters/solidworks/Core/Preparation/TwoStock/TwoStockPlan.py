from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.Circles.CircleInput import (
    CircleInput,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.ThroughStock import (
    ThroughStock,
)


# this prospective construction boundary keeps both independent stocks and the selected tool together
@DataClass(frozen=True, slots=True)
class TwoStockPlan:
    StockValues: tuple[ThroughStock, ThroughStock]
    CircleValue: CircleInput
    CutSketchName: str
    CutName: str
    ResultBodyId: str

    # target selection must use the exact name of the shared neutral document
    @property
    def NameValue(self) -> str:
        return self.StockValues[0].NameValue
