from __future__ import annotations

from interchange.assembly.TransformMatrix import TransformMatrix
from interchange.Core.ModelBase import ModelBase, ModelDataMut
from interchange.geometry.Models.VectorPlane import PlaneVector


# model view placement and reference intent need a portable drawing record
@ModelDataMut
class DrawingView(ModelBase):
    EntityId: str
    EntityName: str
    ModelRefId: str
    ConfigurationName: str
    PositionValue: PlaneVector
    OrientationName: str | None = None
    ScaleRatio: tuple[float, float] | None = None
    ModelToSheet: TransformMatrix | None = None
    OutlineValues: tuple[float, float, float, float] | None = None
