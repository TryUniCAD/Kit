from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.IsStockConfig import (
    IsStockConfig,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.Revolves.SelectedCut.ApplySelRevCut import (
    ApplySelRevCut,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.SelectedCut.ReadRevCache import (
    ReadRevCache,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.SelectedCut.ReadSelRevCut import (
    ReadSelRevCut,
)
from interchange.document.Models.DocumentModel import CadDocument


# saved revolve geometry can be refined only when the exact scoped model and both owners qualify
def WithSelRevDoc(
    DocumentValue: CadDocument, Archive: SldprtArchive, ConfigId: int | None
) -> CadDocument:
    ClassNames = DocumentValue.metadata.get("native_class_names", ())
    if (
        ConfigId != 0
        or DocumentValue.brep is None
        or not isinstance(ClassNames, tuple)
        or "moRevCut_c" not in ClassNames
        or len(DocumentValue.configurations) != 1
    ):
        return DocumentValue
    try:
        if not IsStockConfig(Archive, 19000):
            return DocumentValue
        LinkValue = ReadNativeLink(Archive, ConfigId)
        TopHeader = ReadHeaderGraph(Archive.require("Header2"), 19000)
        Lineage = ReadSelRevCut(LinkValue, TopHeader)
        Cache = ReadRevCache(Archive, LinkValue, Lineage)
        Result = ApplySelRevCut(DocumentValue, LinkValue, Lineage, Cache)
        Result.assert_valid()
        return Result
    except (ValueError, TypeError, KeyError):
        return DocumentValue
