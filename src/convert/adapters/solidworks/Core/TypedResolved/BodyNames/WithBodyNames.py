from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.BindBodyName import (
    BindBodyName,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadNamedBody import (
    ReadNamedBody,
)
from interchange.document.Models.DocumentModel import CadDocument
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.Revolves.ReadRevolveBody import (
    ReadRevolveBody,
)


# unsupported body inventories retain their existing reader path without speculative naming or geometry changes
def WithBodyNames(
    Document: CadDocument, Archive: SldprtArchive, ConfigId: int | None
) -> CadDocument:
    if (
        Document.brep is None
        or len(Document.brep.bodies) != 1
        or len(Document.bodies) != 1
    ):
        return Document
    try:
        return BindBodyName(Document, ReadNamedBody(Document, Archive, ConfigId))
    except (TypeError, ValueError, KeyError):
        try:
            return BindBodyName(Document, ReadRevolveBody(Document, Archive, ConfigId))
        except (TypeError, ValueError, KeyError):
            return Document
