from __future__ import annotations

import math as MathValue

KMillimetres = 1000.0


def MmFromMetres(Metres: float) -> float:
    Candidate = Metres * KMillimetres
    for _ in range(8):
        BackValue = Candidate / KMillimetres
        if BackValue == Metres:
            return Candidate
        Candidate = MathValue.nextafter(
            Candidate, MathValue.inf if BackValue < Metres else -MathValue.inf
        )
    return Candidate
