from interchange.Core.ModelBase import ModelBase, ModelDataMut
from interchange.geometry.Models.VectorSpace import SpaceVector


# a sheet note preserves its authored text and position independently of display caches
@ModelDataMut
class DrawingNote(ModelBase):
    EntityId: str
    TextValue: str
    PositionValue: SpaceVector
