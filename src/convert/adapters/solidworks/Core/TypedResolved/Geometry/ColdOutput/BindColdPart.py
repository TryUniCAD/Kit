from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cold.ColdStockPart import (
    ColdStockPart,
)
from convert.adapters.solidworks.Core.TypedResolved.Patterns.ApplyPatDoc import (
    ApplyPatDoc,
)
from convert.adapters.solidworks.Core.TypedResolved.Patterns.ApplyTiltDoc import (
    ApplyTiltDoc,
)
from convert.adapters.solidworks.Core.TypedResolved.Patterns.Cold.ColdPatPart import (
    ColdPatPart,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.SelectedCut.Cold.BindColdRevolveDoc import (
    BindColdRevolveDoc,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.SelectedCut.Cold.ColdRevolvePart import (
    ColdRevolvePart,
)
from interchange.document.Models.DocumentModel import CadDocument


# reconstructed shape and native graph must use the same exact specialized feature owners
def BindColdPart(
    Document: CadDocument,
    ColdValue: ColdStockPart | ColdRevolvePart | ColdPatPart | None,
) -> CadDocument:
    if isinstance(ColdValue, ColdRevolvePart):
        return BindColdRevolveDoc(Document, ColdValue.OwnersValue)
    if isinstance(ColdValue, ColdPatPart):
        OwnerValue = ColdValue.OwnerValue
        LinkValue = ColdValue.LinkValue
        Bound = ApplyTiltDoc(Document, LinkValue, OwnerValue.DatumValue)
        return ApplyPatDoc(Bound, LinkValue, OwnerValue, None)
    return Document
