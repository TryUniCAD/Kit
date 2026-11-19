from convert.adapters.solidworks.Drawing.Definition.Appearance.AppearanceState import (
    AppearanceState,
)


# the two signed archive words derive from one explicit unsigned allocator and an empty modeled reference list
def MakeAppearMgr(InputValue: AppearanceState) -> dict[str, object]:
    if type(InputValue) is not AppearanceState:
        raise TypeError(
            "rendering manager construction requires typed appearance state"
        )
    if not InputValue.ManagerOnWire:
        if InputValue.NextAppearanceId != 1:
            raise ValueError(
                "absent appearance state cannot retain a different allocator"
            )
        return {"has_pwmaterial": 0}
    CounterValue = InputValue.NextAppearanceId
    LowValue = CounterValue & 0xFFFFFFFF
    HighValue = CounterValue >> 32
    RowValues: list[object] = []
    return {
        "has_pwmaterial": 1,
        "f1110": {
            "f08": LowValue - (1 << 32) if LowValue & (1 << 31) else LowValue,
            "f0c": HighValue - (1 << 32) if HighValue & (1 << 31) else HighValue,
            "list": {"n": len(RowValues), "items": RowValues},
        },
    }
