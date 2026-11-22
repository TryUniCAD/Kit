# the receipt must report a real positive count or measurement of the observed model
def ReadMeasNum(Value: object) -> float:
    if (
        not isinstance(Value, (int, float))
        or isinstance(Value, bool)
        or not 0 < Value < float("inf")
    ):
        raise ValueError("native measurement requires positive finite observations")
    return float(Value)
