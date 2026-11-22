from convert.adapters.solidworks.Core.Writing.AttachedBox.BoxProof import BoxProof
from convert.adapters.solidworks.Core.Writing.AttachedBox.IsBoxSource import IsBoxSource
from convert.adapters.solidworks.Core.Writing.AttachedBox.ProveBoxSource import (
    ProveBoxSource,
)
from interchange.document.Models.DocumentModel import CadDocument


# only the actual solidworks adapter can offer this source verification route
def FindBoxProof(WriterValue: object, Document: CadDocument) -> BoxProof | None:
    from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter

    if type(WriterValue) is not SldprtWriter or not IsBoxSource(Document):
        return None
    return ProveBoxSource(Document)
