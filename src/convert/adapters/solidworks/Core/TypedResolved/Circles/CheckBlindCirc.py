from convert.adapters.solidworks.Archive.Construction.Blind.BlindZeroFields import (
    KBlindZeroFields,
)
from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismAtom import (
    CheckPrismAtom,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Checks.CheckBossState import (
    CheckBossState,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismParam import (
    ReadPrismParam,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# an analytic circle cannot replace selected bodies draft or alternate live end states
def CheckBlindCirc(OwnerValue: ExtrudeOwner) -> None:
    BossValue = OwnerValue.NodeValue
    Fields = OwnerValue.EndValue.FieldsValue
    if (
        OwnerValue.ParentsValue != (OwnerValue.ProfileValue,)
        or any(Fields.get(NameValue) != 0 for NameValue in KBlindZeroFields)
        or Fields.get("f128") != 1
        or Fields.get("fa0") != 0.0
        or Fields.get("f138") is not None
        or Fields.get("f90") is not None
        or any(not IsLineState(Fields.get(NameValue)) for NameValue in ("fe0", "f100"))
    ):
        raise ValueError("cold circle has unsupported blind boss ownership")
    FromValue = RequireNative(Fields.get("f140"), "moFromEndSpec_c")
    if FromValue.FieldsValue != {"t": 0}:
        raise ValueError("cold circle has an unsupported start owner")
    CheckPrismAtom(BossValue)
    CheckBossState(BossValue)
    Values = tuple(
        ReadPrismParam(Fields.get(FieldName), Index > 1)
        for Index, FieldName in enumerate(("f18", "f20", "fc8", "fd0"))
    )
    Forward, Reverse, Draft, OtherDraft = Values
    if (
        Forward[1] is not OwnerValue.DepthValue.Parameter
        or len({Dimension for Dimension, _, _ in Values}) != 4
        or len({Parameter for _, Parameter, _ in Values}) != 4
        or len({Dimension.FieldsValue.get("f50") for Dimension, _, _ in Values}) != 4
        or Reverse[2] != Forward[2]
        or Draft[2] != 0
        or OtherDraft[2] != 0
    ):
        raise ValueError("cold circle has contradictory blind depth or draft ownership")
