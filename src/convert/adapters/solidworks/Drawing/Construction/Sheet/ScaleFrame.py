# sheet and ui sketches require opposite scale directions through the same native identity transform
def MakeScaleFrame(ScaleValue: float) -> dict[str, object]:
    return {
        "has_matrix": 0,
        "f58": 0.0,
        "f60": 0.0,
        "f68": 0.0,
        "f70": ScaleValue,
        "f78": 0,
    }
