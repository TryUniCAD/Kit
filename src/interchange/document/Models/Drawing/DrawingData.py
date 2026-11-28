from __future__ import annotations

from interchange.Core.ModelBase import ModelBase, ModelDataMut
from interchange.document.Models.Drawing.DrawingModelRef import DrawingModelRef
from interchange.document.Models.Drawing.DrawingSheet import DrawingSheet


# sheet ownership and shared model links make a complete portable drawing layout
@ModelDataMut
class DrawingData(ModelBase):
    ActiveSheetId: str
    Sheets: tuple[DrawingSheet, ...]
    ModelRefs: tuple[DrawingModelRef, ...] = ()
