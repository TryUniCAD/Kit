from __future__ import annotations

from interchange.Core.ModelBase import ModelBase, ModelDataMut
from interchange.document.Models.Drawing.DrawingView import DrawingView


# paper properties and ordered views need an owner independent of model configurations
@ModelDataMut
class DrawingSheet(ModelBase):
    EntityId: str
    EntityName: str
    SheetWidth: float
    SheetHeight: float
    ScaleRatio: tuple[float, float]
    Views: tuple[DrawingView, ...] = ()
