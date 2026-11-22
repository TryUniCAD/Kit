from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KPartitionStream
from convert.adapters.solidworks.Core.TypedResolved.Fillets.Saved.BindFilletDoc import (
    BindFilletDoc,
)
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import FeatureKind


# warm fillet layout and body proof must both pass before supplementing the existing part read
def WithSavedFillet(
    Document: CadDocument,
    Archive: SldprtArchive,
    ConfigId: int | None,
) -> CadDocument:
    Classes = Document.metadata.get("native_class_names")
    if (
        ConfigId != 0
        or Document.brep is None
        or len(Document.bodies) != 1
        or len(Document.configurations) != 1
        or Document.configurations[0].name != "Default"
        or KPartitionStream not in Archive.streams
        or not isinstance(Classes, tuple)
        or "Fillet_c" not in Classes
        or tuple(
            Value.kind
            for Value in Document.feature_timeline
            if Value.kind in (FeatureKind.KExtrusion, FeatureKind.KFillet)
        )
        != (FeatureKind.KExtrusion, FeatureKind.KFillet)
    ):
        return Document
    try:
        Bound = BindFilletDoc(Document, Archive)
        Bound.assert_valid()
        return Bound
    except (ValueError, TypeError, KeyError, OverflowError):
        return Document
