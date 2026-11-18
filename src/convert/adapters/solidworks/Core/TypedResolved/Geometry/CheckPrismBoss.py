from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismAtom import (
    CheckPrismAtom,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ColdOutput.ColdOutput import (
    ColdOutput,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState
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
    Fields = OwnerValue.NodeValue.FieldsValue
    if (
        OwnerValue.ModeValue != ModeValue
        or OwnerValue.IsReversed
        or OwnerValue.SecondValue is not None
    ):
        raise ValueError(f"cache free prism requires one forward {ModeValue} direction")
    if (
        Fields.get("f28") != 0x40000000 | 0x140
        or Fields.get("f810") != -1
        or Fields.get("f838") != 0.0
    ):
        raise ValueError("cache free prism requires its ordinary create boss mode")
    if (
        Fields.get("f538") is not None
        or Fields.get("f6e0") is not None
        or Fields.get("f758") is not None
        or Fields.get("f7a0") != 0
    ):
        raise ValueError("cache free prism has additional extrusion geometry state")
    if (
        not IsLineState(Fields.get("f368"))
        or not IsLineState(Fields.get("f388"))
        or not IsLineState(Fields.get("f780"))
    ):
        raise ValueError("cache free prism has selected geometry or body references")
