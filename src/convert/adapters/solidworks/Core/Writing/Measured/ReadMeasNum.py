from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasReal import ReadMeasReal


# the receipt must report a real positive count or measurement of the observed model
def ReadMeasNum(Value: object) -> float:
    NumberValue = ReadMeasReal(Value)
    if NumberValue <= 0:
        raise ValueError("native measurement requires positive finite observations")
    return NumberValue
