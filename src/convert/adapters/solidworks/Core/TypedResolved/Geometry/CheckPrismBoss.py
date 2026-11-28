from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
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


# selected empty scope needs an actual forward blind boss with only its sketch parent
def CheckFirstBoss(OwnerValue: ExtrudeOwner) -> None:
    if (
        OwnerValue.NodeValue.ClassValue != RuntimeClass("moExtrusion_c", 1)
        or OwnerValue.ModeValue != ExtrudeEnd.KBlind
        or OwnerValue.IsReversed
        or OwnerValue.ParentsValue != (OwnerValue.ProfileValue,)
    ):
        raise ValueError(
            "cache free first creator requires one ordinary forward blind profile"
        )


# the analytic boss cannot stand in for cuts thin surfaces stored bodies selected merges or additional body modifiers
def CheckPrismBoss(
    OwnerValue: ExtrudeOwner,
    ColdValue: ColdOutput | None = None,
    *,
    ModeValue: ExtrudeEnd = ExtrudeEnd.KBlind,
    SelectedStock: bool = False,
    AllowFirstScope: bool = False,
) -> None:
    FirstScope = AllowFirstScope and OwnerValue.NodeValue.FieldsValue.get("f544") == 1
    if FirstScope:
        if ColdValue is not None or SelectedStock or ModeValue != ExtrudeEnd.KBlind:
            raise ValueError("cache free first creator cannot carry other solid state")
        CheckFirstBoss(OwnerValue)
    CheckPrismAtom(
        OwnerValue.NodeValue,
        ColdValue is not None and ColdValue.BossValue is OwnerValue.NodeValue,
        SelectedScope=(
            "first_creator" if FirstScope else ("stock" if SelectedStock else None)
        ),
    )
    CheckBossState(OwnerValue.NodeValue)
