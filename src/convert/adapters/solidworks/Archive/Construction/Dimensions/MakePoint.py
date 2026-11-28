# independently owned constructor points must never alias mutable display geometry from another annotation
def MakePoint(
    *, XValue: float = 0.0, YValue: float = 0.0, ZValue: float = 0.0
) -> dict[str, float]:
    return {"x": XValue, "y": YValue, "z": ZValue}
