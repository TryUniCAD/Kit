from math import isclose as IsClose


# legacy radial matching needs one policy owner while retaining its existing tolerance and precedence
def MatchRadialVal(ValueMm: float | None, RadiusMm: float) -> tuple[str, float] | None:
    if ValueMm is None:
        return None
    if IsClose(ValueMm, RadiusMm, rel_tol=1e-7, abs_tol=1e-7):
        return "radius", ValueMm
    if IsClose(ValueMm, RadiusMm * 2.0, rel_tol=1e-7, abs_tol=1e-7):
        return "diameter", ValueMm / 2.0
    return None
