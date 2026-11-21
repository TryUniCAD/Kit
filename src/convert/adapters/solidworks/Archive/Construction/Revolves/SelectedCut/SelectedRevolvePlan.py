from dataclasses import dataclass as Dataclass

from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.RevolvePlan import (
    RevolvePlan,
)


# the selected operation must retain both independent stock plans and its actual consumed producer
@Dataclass(frozen=True, slots=True)
class SelectedRevolvePlan:
    OperationsValue: tuple[RevolvePlan, RevolvePlan, RevolvePlan]
    SelectedIndex: int

    # the final destination basename represents the same document as the stock plans
    @property
    def NameValue(self) -> str:
        return self.OperationsValue[0].NameValue
