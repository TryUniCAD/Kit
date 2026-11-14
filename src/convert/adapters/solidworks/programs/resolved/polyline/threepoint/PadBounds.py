from __future__ import annotations

from dataclasses import dataclass as Dataclass


@Dataclass(frozen=True, slots=True)
class PadBounds:
    CentreX: float
    CentreY: float
    CentreZ: float
    ExpandedX: float
    ExpandedY: float
    ExpandedZ: float
    Diameter: float
