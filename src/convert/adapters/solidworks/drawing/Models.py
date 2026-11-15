from __future__ import annotations

from dataclasses import dataclass

from interchange import Vector3


# frozen model bounds keep recovered extents tied to their centre
@dataclass(frozen=True, slots=True)
class ViewBounds:
    Center: Vector3
    Minimum: Vector3
    Maximum: Vector3


# frozen view data keeps recovered metadata safe to share between callers
@dataclass(frozen=True, slots=True)
class DrawingView:
    Name: str
    ModelPath: str
    Description: str
    PositionX: float | None = None
    PositionY: float | None = None
    OutlineMinX: float | None = None
    OutlineMinY: float | None = None
    OutlineMaxX: float | None = None
    OutlineMaxY: float | None = None
    ModelBounds: ViewBounds | None = None


# frozen sheet data keeps each sheet composition explicit and immutable
@dataclass(frozen=True, slots=True)
class DrawingSheet:
    Name: str
    PaperSize: str
    ScaleNumerator: float
    ScaleDenominator: float
    WidthMetres: float
    HeightMetres: float
    Views: tuple[DrawingView, ...]


# frozen reference data keeps external drawing links separate from sheet text
@dataclass(frozen=True, slots=True)
class DrawingRef:
    Name: str
    Description: str


# frozen document data keeps the public drawing surface one immutable value
@dataclass(frozen=True, slots=True)
class DrawingData:
    Name: str
    Sheets: tuple[DrawingSheet, ...]
    References: tuple[DrawingRef, ...]
    Notes: tuple[str, ...]
    SourcePath: str
