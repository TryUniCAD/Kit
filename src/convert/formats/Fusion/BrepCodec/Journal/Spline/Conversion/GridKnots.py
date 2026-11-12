from convert.formats.Fusion.BrepCodec.Journal.Spline.SplineKnot import SplineKnot


def GridKnots(SpanCount: int) -> tuple[SplineKnot, ...]:
    if SpanCount < 1:
        raise ValueError("Fusion grid conversion needs one span per direction")
    Inner = tuple(SplineKnot(float(Index), 1) for Index in range(1, SpanCount))
    return (SplineKnot(0.0, 3), *Inner, SplineKnot(float(SpanCount), 3))
