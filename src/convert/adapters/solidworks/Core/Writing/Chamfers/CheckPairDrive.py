from typing import cast as CastValue

from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap


# an exact measurement must attest each actual active linear driver and its common feature name
def CheckPairDrive(
    CaseValue: dict[str, object], SlotValue: int, FeatureName: str
) -> None:
    Expected = (
        (("shared", "D1"),) if SlotValue == 0 else (("first", "D1"), ("second", "D3"))
    )
    Drivers = ReadMeasMap(CaseValue.get("drivers"))
    if set(Drivers) != {RoleValue for RoleValue, _ in Expected}:
        raise ValueError("distance chamfer measurement has an unowned driver inventory")
    for RoleValue, NameValue in Expected:
        ItemValue = Drivers[RoleValue]
        if type(ItemValue) is not list:
            raise ValueError("distance chamfer measurement has an unowned driver")
        Parts = CastValue(list[object], ItemValue)
        if Parts != [NameValue, FeatureName, 2, 0] or any(
            type(Value) is not int for Value in Parts[2:]
        ):
            raise ValueError("distance chamfer measurement has an unowned driver")
