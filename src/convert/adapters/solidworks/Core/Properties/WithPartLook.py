from dataclasses import replace as ReplaceValue

from convert.adapters.base.Materials.CheckPartLook import KPartLookKey
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Properties.ReadPartLook import ReadPartLook
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument


# existing inspection remains available when the bounded visual record cannot be resolved
def WithPartLook(Document: CadDocument, Archive: SldprtArchive) -> CadDocument:
    if Archive.format_version != 4 or Archive.get("Contents/Config-0") is None:
        return Document
    try:
        Evidence = ReadPartLook(Archive)
    except (TypeError, ValueError, KeyError, SyntaxError):
        return Document
    return ReplaceValue(
        Document,
        metadata=FreezeMapping({**Document.metadata, KPartLookKey: Evidence}),
    )
