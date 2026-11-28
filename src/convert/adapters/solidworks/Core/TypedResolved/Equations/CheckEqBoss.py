from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState


# active end and create conditions qualify the equation target across fresh and saved boss owners
def CheckEqBoss(BossValue: ExtrudeOwner) -> None:
    FieldsValue = BossValue.NodeValue.FieldsValue
    EndFields = BossValue.EndValue.FieldsValue
    if (
        BossValue.IsReversed
        or BossValue.ParentsValue != (BossValue.ProfileValue,)
        or FieldsValue.get("f28") not in (0x40000140, 0xC0000140)
        or FieldsValue.get("f810") != -1
        or FieldsValue.get("f838") != 0.0
        or FieldsValue.get("f7a0") != 0
        or any(
            FieldsValue.get(KeyName) is not None for KeyName in ("f538", "f6e0", "f758")
        )
        or any(
            not IsLineState(FieldsValue.get(KeyName))
            for KeyName in ("f368", "f388", "f780")
        )
        or EndFields.get("f128") != 1
        or any(EndFields.get(KeyName) is not None for KeyName in ("f90", "f138"))
        or any(
            EndFields.get(KeyName) != 0
            for KeyName in (
                "fa0",
                "fb8",
                "fbc",
                "fc0",
                "fc4",
                "fb0",
                "fb4",
                "fa8",
                "fac",
                "fd8",
                "fdc",
            )
        )
        or any(
            not (
                (
                    EndFields.get("has_" + KeyName) == 0
                    and EndFields.get(KeyName) is None
                )
                or (
                    EndFields.get("has_" + KeyName) == 1
                    and IsLineState(EndFields.get(KeyName))
                )
            )
            for KeyName in ("f28", "f48")
        )
        or any(not IsLineState(EndFields.get(KeyName)) for KeyName in ("fe0", "f100"))
    ):
        raise ValueError(
            "local width-depth equation requires an ordinary forward blind boss"
        )
    if BossValue.DepthValue.Parameter.FieldsValue.get("f48") is not None:
        raise ValueError(
            "local width-depth equation targets an alternate depth parameter"
        )
