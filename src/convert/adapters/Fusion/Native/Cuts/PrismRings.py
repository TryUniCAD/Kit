from convert.Formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)
from interchange.geometry.Models.VectorPlane import PlaneVector


# expected oriented boundaries follow directly from the editable planar profile and extent
def PrismRings(
    Points: tuple[PlaneVector, ...], Lower: float, Upper: float
) -> tuple[tuple[KJournalVector, ...], ...]:
    Bottom = tuple((Point.x / 10, Point.y / 10, Lower / 10) for Point in Points)
    TopRing = tuple((Point.x / 10, Point.y / 10, Upper / 10) for Point in Points)
    return (
        tuple(reversed(Bottom)),
        TopRing,
        *(
            (
                Bottom[Index],
                Bottom[(Index + 1) % len(Points)],
                TopRing[(Index + 1) % len(Points)],
                TopRing[Index],
            )
            for Index in range(len(Points))
        ),
    )
