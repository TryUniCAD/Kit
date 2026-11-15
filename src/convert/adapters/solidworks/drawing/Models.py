from __future__ import annotations

from dataclasses import dataclass

from convert.adapters.solidworks.drawing.DefinitionStyles import LineStyle
from convert.adapters.solidworks.drawing.DefinitionUnits import UnitTable
from interchange import Vector3


# frozen model bounds keep recovered extents tied to their centre
@dataclass(frozen=True, slots=True)
class ViewBounds:
    Center: Vector3
    Minimum: Vector3
    Maximum: Vector3


# frozen edge data keeps one recovered model segment explicit
@dataclass(frozen=True, slots=True)
class ViewEdge:
    Start: Vector3
    End: Vector3


# frozen orientation data keeps the recovered view rotation explicit
@dataclass(frozen=True, slots=True)
class ViewOrientation:
    Matrix: tuple[tuple[float, float, float], ...]


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
    ViewScale: float | None = None
    Edges: tuple[ViewEdge, ...] = ()
    Orientation: ViewOrientation | None = None
    SheetEdges: tuple[ViewEdge, ...] = ()


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
    Units: tuple[UnitTable, ...] | None = None
    LineStyles: tuple[LineStyle, ...] | None = None
