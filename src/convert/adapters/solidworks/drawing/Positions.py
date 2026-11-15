from __future__ import annotations

import math as MathValue
import struct as Struct

# repeated position records are separated by this native display list stride
KRecordOffset = 384

# displayed coordinates stay far below this guard against arbitrary binary noise
KMaxCoordinate = 1000000.0


# view centres are recovered as paired display list records and deduplicated by pair
def Positions(DataValue: bytes) -> tuple[tuple[float, float], ...]:
    Candidates: dict[int, tuple[float, float]] = {}
    for Offset in range(0, len(DataValue) - 32):
        XValue, YValue = Struct.unpack_from("<dd", DataValue, Offset)
        ZValue = Struct.unpack_from("<d", DataValue, Offset + 16)[0]
        WValue = Struct.unpack_from("<d", DataValue, Offset + 24)[0]
        if not (
            MathValue.isfinite(XValue)
            and MathValue.isfinite(YValue)
            and abs(XValue) < KMaxCoordinate
            and abs(YValue) < KMaxCoordinate
        ):
            continue
        if ZValue != 0.0 or WValue not in (1.0, 2.0):
            continue
        Candidates[Offset] = (XValue, YValue)
    Points: list[tuple[float, float]] = []
    Consumed: set[int] = set()
    for Offset in sorted(Candidates):
        if Offset in Consumed:
            continue
        Paired = Offset + KRecordOffset
        if Candidates.get(Paired) == Candidates[Offset]:
            Points.append(Candidates[Offset])
            Consumed.add(Paired)
    return tuple(Points)
