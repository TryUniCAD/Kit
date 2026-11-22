from struct import pack as PackValues

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord


# the selected display contributes its own finite text placement and corroborates the live length
def ReadDimLabel(
    DisplayValue: ArchiveNode, MetresValue: float
) -> tuple[tuple[float, ...], int, bool, bool]:
    FieldsValue = DisplayValue.FieldsValue
    TextValue = NativeRecord(FieldsValue.get("f6a0"))
    Position = NativeRecord(TextValue.get("f38"))
    CacheValue = NativeRecord(FieldsValue.get("f5b0"))
    RouteValue = FieldsValue.get("f1014")
    LeaderValue = FieldsValue.get("ff80")
    StyleValue = FieldsValue.get("fb60")
    if (
        TextValue.get("f10") != 18
        or type(LeaderValue) is not int
        or type(StyleValue) is not int
        or RouteValue not in (0, 0x800)
        or CacheValue.get("elem") != 8
        or CacheValue.get("n") != 1
        or CacheValue.get("data") != PackValues("<d", MetresValue)
    ):
        raise ValueError("typed rectangle display disagrees with its live dimension")
    return (
        tuple(RequireScalar(Position.get(AxisValue)) for AxisValue in ("x", "y", "z")),
        LeaderValue,
        bool(RouteValue),
        bool(StyleValue & 0x100),
    )
