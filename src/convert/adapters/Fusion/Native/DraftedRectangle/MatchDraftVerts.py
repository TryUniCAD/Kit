from math import isclose as IsClose

from convert.Formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)


# independent native coordinate caches must resolve bijectively within the qualified geometric tolerance
def MatchDraftVerts(
    Points: tuple[KJournalVector, ...], Expected: tuple[KJournalVector, ...]
) -> tuple[int, ...]:
    Mapping = tuple(
        tuple(
            Index
            for Index, Target in enumerate(Expected)
            if all(
                IsClose(Actual, Value, rel_tol=1e-10, abs_tol=1e-9)
                for Actual, Value in zip(Point, Target, strict=True)
            )
        )
        for Point in Points
    )
    if any(len(Matches) != 1 for Matches in Mapping) or len(set(Mapping)) != len(
        Points
    ):
        raise ValueError(
            "Native drafted coordinates do not have unique generated counterparts"
        )
    return tuple(Matches[0] for Matches in Mapping)
