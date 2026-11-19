from __future__ import annotations

from dataclasses import field as MakeDataField

from interchange.Core.ModelBase import ModelBase, ModelDataMut
from interchange.document.Models.Drawing.DrawingNote import DrawingNote
from interchange.document.Models.Drawing.DrawingView import DrawingView
from interchange.serialization.OptionalFields import KOmitNullField


# paper properties and ordered views need an owner independent of model configurations
@ModelDataMut
class DrawingSheet(ModelBase):
    EntityId: str
    EntityName: str
    SheetWidth: float
    SheetHeight: float
    ScaleRatio: tuple[float, float]
    Views: tuple[DrawingView, ...] = ()
    Notes: tuple[DrawingNote, ...] | None = MakeDataField(
        default=None, metadata={KOmitNullField: True}
    )
