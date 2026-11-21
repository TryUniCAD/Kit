from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.IsStockConfig import (
    IsStockConfig,
)
from convert.adapters.solidworks.Core.TypedResolved.Patterns.ApplyPatDoc import (
    ApplyPatDoc,
)
from convert.adapters.solidworks.Core.TypedResolved.Patterns.ReadPatBody import (
    ReadPatBody,
)
from convert.adapters.solidworks.Core.TypedResolved.Patterns.ReadPatOwner import (
    ReadPatOwner,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from interchange.document.Models.DocumentModel import CadDocument


# unsupported or unsaved variants keep the existing generic reader behavior
def WithPatternDoc(
    Document: CadDocument, Archive: SldprtArchive, ConfigId: int | None
) -> CadDocument:
    ClassNames = Document.metadata.get("native_class_names", ())
    if (
        ConfigId != 0
        or Document.brep is None
        or len(Document.configurations) != 1
        or not isinstance(ClassNames, tuple)
        or "moLPattern_c" not in ClassNames
    ):
        return Document
    try:
        if not IsStockConfig(Archive, 19000):
            return Document
        LinkValue = ReadNativeLink(Archive, ConfigId)
        Header = ReadHeaderGraph(Archive.require("Header2"), 19000)
        OwnerValue = ReadPatOwner(LinkValue, Header)
        BodyValue = ReadPatBody(Document, Archive, LinkValue, OwnerValue)
        Result = ApplyPatDoc(Document, LinkValue, OwnerValue, BodyValue)
        Result.assert_valid()
        return Result
    except (ValueError, TypeError, KeyError):
        return Document
