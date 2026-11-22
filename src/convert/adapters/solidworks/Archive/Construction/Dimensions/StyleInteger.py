from collections.abc import Mapping

from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt


# style projections must fit their actual signed or unsigned native wire field domains before display construction
def StyleInteger(
    Values: Mapping[str, object],
    FieldName: str,
    LowBound: int = 0,
    HighBound: int = 0x7FFFFFFF,
) -> int:
    NumberValue = FieldInt(Values, FieldName)
    if not LowBound <= NumberValue <= HighBound:
        raise ValueError("linear display style value exceeds its native integer domain")
    return NumberValue
