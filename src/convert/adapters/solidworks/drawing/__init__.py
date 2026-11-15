from __future__ import annotations

from convert.adapters.solidworks.drawing.Drawing import (
    DrawingData,
    DrawingRef,
    DrawingSheet,
    DrawingView,
    ReadDrawing,
)

Drawing = DrawingData
ReadSlddrw = ReadDrawing
read_slddrw = ReadDrawing

__all__ = [
    "Drawing",
    "DrawingData",
    "DrawingRef",
    "DrawingSheet",
    "DrawingView",
    "ReadDrawing",
    "ReadSlddrw",
    "read_slddrw",
]
