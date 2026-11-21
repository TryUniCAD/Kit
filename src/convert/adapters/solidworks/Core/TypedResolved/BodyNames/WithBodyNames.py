from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.BindBodyName import (
    BindBodyName,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.Local.ReadLocalNamedBody import (
    ReadLocalName,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadNamedBody import (
    ReadNamedBody,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.SavedScope.WithSavedScope import (
    WithSavedScope,
)
from interchange.document.Models.DocumentModel import CadDocument
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.Revolves.ReadRevolveBody import (
    ReadRevolveBody,
)


# unsupported body inventories retain their existing reader path without speculative naming or geometry changes
def WithBodyNames(
    Document: CadDocument,
    Archive: SldprtArchive,
    ConfigId: int | None,
    *,
    BindSavedScope: bool = False,
) -> CadDocument:
    if (
        Document.brep is None
        or len(Document.brep.bodies) != 1
        or len(Document.bodies) != 1
    ):
        return Document
    try:
        GraphValue = ReadNamedBody(Document, Archive, ConfigId)
        Bound = BindBodyName(Document, GraphValue)
    except (TypeError, ValueError, KeyError):
        try:
            return BindBodyName(Document, ReadRevolveBody(Document, Archive, ConfigId))
        except (TypeError, ValueError, KeyError):
            try:
                return BindBodyName(
                    Document, ReadLocalName(Document, Archive, ConfigId)
                )
            except (TypeError, ValueError, KeyError, OverflowError):
                return Document
    if BindSavedScope:
        return WithSavedScope(Bound, Archive, GraphValue)
    return Bound
