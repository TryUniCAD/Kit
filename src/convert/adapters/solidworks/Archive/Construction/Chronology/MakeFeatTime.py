from convert.adapters.solidworks.Archive.Construction.Chronology.FeatureInstant import (
    FeatureInstant,
)


# precise modeled feature moments must preserve native tick carry without borrowing serialized time words
def MakeFeatTime(InputValue: FeatureInstant) -> dict[str, int]:
    if type(InputValue) is not FeatureInstant:
        raise ValueError("feature timestamp construction requires a typed instant")
    TicksValue = (
        InputValue.SecondsValue + 11644473600
    ) * 10_000_000 + InputValue.FractionTicks
    LowValue, HighValue = TicksValue & 0xFFFFFFFF, TicksValue >> 32
    return {
        "f2a0": LowValue - (1 << 32) if LowValue & (1 << 31) else LowValue,
        "f2a4": HighValue - (1 << 32) if HighValue & (1 << 31) else HighValue,
    }
