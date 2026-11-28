from math import isclose as IsClose, ulp as FloatStep


# equivalent paper sizes can come from native inch conversion or the decimal layout index
def IsAnsiLandscape(Width: float, Height: float) -> bool:
    NativeWidth = 11 * 0.0254
    NativeHeight = 8.5 * 0.0254
    return IsClose(
        Width, NativeWidth, rel_tol=0, abs_tol=FloatStep(NativeWidth)
    ) and IsClose(Height, NativeHeight, rel_tol=0, abs_tol=FloatStep(NativeHeight))
