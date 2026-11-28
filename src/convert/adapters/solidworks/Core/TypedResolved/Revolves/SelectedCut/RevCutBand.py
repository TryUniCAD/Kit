from dataclasses import dataclass as Dataclass


# one rectangular meridian identifies its radial walls and two axial bounds
@Dataclass(frozen=True, slots=True)
class RevCutBand:
    Radial: tuple[float, float]
    Axial: tuple[float, float]
    Walls: tuple[int, int]
    Marks: frozenset[int]
