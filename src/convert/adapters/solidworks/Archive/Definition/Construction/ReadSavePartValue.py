from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleNum import (
    ReadStyleNum,
)


# the assembly preference getter defines which values are doubles booleans or signed longs
def ReadSavePref(SlotName: str, Value: object) -> int | float:
    if SlotName in ("5fd", "5ff"):
        Number = ReadStyleNum(Value, f"SOLIDWORKS assembly preference {SlotName}")
        if SlotName == "5fd":
            if Number > 0.9:
                return 0.9
            if Number < 0.0:
                return 0.0
        return Number
    if SlotName == "605":
        if type(Value) is not int or not -(2**31) <= Value < 2**31:
            raise ValueError(
                "SOLIDWORKS assembly preference 605 must fit a signed long"
            )
        return Value
    if type(Value) is not bool:
        raise TypeError(f"SOLIDWORKS assembly preference {SlotName} must be boolean")
    return int(Value)
