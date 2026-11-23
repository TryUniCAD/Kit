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


# both read modes require an exact local archive owner before assigning its label
def WithLocalName(
    Document: CadDocument,
    Archive: SldprtArchive,
    ConfigId: int | None,
    *,
    DesignOnly: bool,
) -> CadDocument:
    try:
        return BindBodyName(
            Document, ReadLocalName(Document, Archive, ConfigId, DesignOnly=DesignOnly)
        )
    except (TypeError, ValueError, KeyError, OverflowError):
        return Document


# unsupported body inventories retain their existing reader path without speculative naming or geometry changes
def WithBodyNames(
    Document: CadDocument,
    Archive: SldprtArchive,
    ConfigId: int | None,
    *,
    BindSavedScope: bool = False,
    DesignOnly: bool = False,
) -> CadDocument:
    if len(Document.bodies) != 1:
        return Document
    if Document.brep is None:
        return (
            WithLocalName(Document, Archive, ConfigId, DesignOnly=True)
            if DesignOnly
            else Document
        )
    if len(Document.brep.bodies) != 1:
        return Document
    try:
        GraphValue = ReadNamedBody(Document, Archive, ConfigId)
        Bound = BindBodyName(Document, GraphValue)
    except (TypeError, ValueError, KeyError):
        try:
            return BindBodyName(Document, ReadRevolveBody(Document, Archive, ConfigId))
        except (TypeError, ValueError, KeyError):
            return WithLocalName(Document, Archive, ConfigId, DesignOnly=False)
    if BindSavedScope:
        return WithSavedScope(Bound, Archive, GraphValue)
    return Bound
