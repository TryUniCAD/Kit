from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismAtom import (
    CheckPrismAtom,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ColdOutput.ColdOutput import (
    ColdOutput,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Checks.CheckBossState import (
    CheckBossState,
)
from interchange.Features.FeatureExtrude import ExtrudeEnd


# the analytic boss cannot stand in for cuts thin surfaces stored bodies selected merges or additional body modifiers
def CheckPrismBoss(
    OwnerValue: ExtrudeOwner,
    ColdValue: ColdOutput | None = None,
    *,
    ModeValue: ExtrudeEnd = ExtrudeEnd.KBlind,
    SelectedStock: bool = False,
) -> None:
    CheckPrismAtom(
        OwnerValue.NodeValue,
        ColdValue is not None and ColdValue.BossValue is OwnerValue.NodeValue,
        SelectedScope="stock" if SelectedStock else None,
    )
    CheckBossState(OwnerValue.NodeValue)
