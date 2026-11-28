from convert.Formats.Fusion.MaterialCodec.Models.ColorValue import ColorValue
from convert.Formats.Fusion.MaterialCodec.Models.PropertyValue import KMaterialValue


# exact channel values must remain visible in independent named comparisons
def LegacyValue(Value: KMaterialValue) -> object:
    if isinstance(Value, ColorValue):
        return (Value.RedValue, Value.GreenValue, Value.BlueValue, Value.AlphaValue)
    return Value
