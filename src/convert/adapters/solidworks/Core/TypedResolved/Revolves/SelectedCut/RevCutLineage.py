from dataclasses import dataclass as Dataclass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.StockCutAtoms import (
    StockCutAtoms,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.RevolveOwner import (
    RevolveOwner,
)


# persisted stock order and selected atom ownership describe separate physical and timeline identities
@Dataclass(frozen=True, slots=True)
class RevCutLineage:
    StockValues: tuple[RevolveOwner, RevolveOwner]
    CutValue: RevolveOwner
    AtomsValue: StockCutAtoms
    WrapperValue: ArchiveNode

    # selected stock ownership follows the retired input alias
    @property
    def SelectedValue(self) -> RevolveOwner:
        return self.StockValues[self.AtomsValue.SelectedIndex]

    # the other stock survives without becoming an input to the cut
    @property
    def UntouchedValue(self) -> RevolveOwner:
        return self.StockValues[1 - self.AtomsValue.SelectedIndex]
