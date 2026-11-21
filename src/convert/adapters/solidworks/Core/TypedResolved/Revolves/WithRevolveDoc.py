from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Projection.ApplyRevDoc import (
    ApplyRevDoc,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.ReadRevOwners import (
    ReadRevOwners,
)
from interchange.document.Models.DocumentModel import CadDocument


# unmeasured versions and revolve families must retain their prior public representation without false semantic qualification
def WithRevolveDoc(
    DocumentValue: CadDocument, Archive: SldprtArchive, ConfigId: int | None
) -> CadDocument:
    ClassNames = DocumentValue.metadata.get("native_class_names", ())
    if (
        ConfigId != 0
        or not isinstance(ClassNames, tuple)
        or "moRevolution_c" not in ClassNames
    ):
        return DocumentValue
    try:
        LinkValue = ReadNativeLink(Archive, ConfigId)
        (OwnerValue,) = ReadRevOwners(LinkValue)
        ProjectedValue = ApplyRevDoc(DocumentValue, LinkValue, OwnerValue)
        ProjectedValue.assert_valid()
        return ProjectedValue
    except (ValueError, TypeError, KeyError):
        return DocumentValue
