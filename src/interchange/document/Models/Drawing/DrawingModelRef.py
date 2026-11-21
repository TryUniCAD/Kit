from __future__ import annotations

from interchange.Core.ModelBase import ModelBase, ModelDataMut


# drawing views need reusable model identities without reading referenced documents
@ModelDataMut
class DrawingModelRef(ModelBase):
    EntityId: str
    SourcePath: str
    SourceFormatId: str
