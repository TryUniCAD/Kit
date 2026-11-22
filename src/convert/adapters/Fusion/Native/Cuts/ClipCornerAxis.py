from math import isclose as IsClose


# qualified contact uses the original stock edge as the canonical clipping station
def ClipCornerAxis(
    StockLower: float, StockUpper: float, ToolLower: float, ToolUpper: float
) -> tuple[float, float]:
    Lower = max(StockLower, ToolLower)
    Upper = min(StockUpper, ToolUpper)
    Lower = (
        StockLower if IsClose(Lower, StockLower, rel_tol=0.0, abs_tol=1e-9) else Lower
    )
    Upper = (
        StockUpper if IsClose(Upper, StockUpper, rel_tol=0.0, abs_tol=1e-9) else Upper
    )
    return Lower, Upper
