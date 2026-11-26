from math import isclose as IsClose
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)


# physical face cycles may start at another vertex but cannot reverse their oriented boundary
def IsCutRing(
    Actual: tuple[KJournalVector, ...], Expected: tuple[KJournalVector, ...]
) -> bool:
    return len(Actual) == len(Expected) and any(
        all(
            all(
                IsClose(
                    Actual[Index][AxisIndex],
                    Expected[(Index + Shift) % len(Expected)][AxisIndex],
                    rel_tol=1e-9,
                    abs_tol=1e-9,
                )
                for AxisIndex in range(3)
            )
            for Index in range(len(Actual))
        )
        for Shift in range(len(Expected))
    )
