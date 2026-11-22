from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.TypedResolved.Patterns.ApplyPatDoc import (
    ApplyPatDoc,
)
from convert.adapters.solidworks.Core.TypedResolved.Patterns.ApplyTiltDoc import (
    ApplyTiltDoc,
)
from convert.adapters.solidworks.Core.TypedResolved.Patterns.Cold.ApplyPatStock import (
    ApplyPatStock,
)
from convert.adapters.solidworks.Core.TypedResolved.Patterns.Cold.ColdPatError import (
    ColdPatError,
)
from convert.adapters.solidworks.Core.TypedResolved.Patterns.Cold.ColdPatPart import (
    ColdPatPart,
)
from interchange.document.Models.DocumentModel import CadDocument


# failed cold presentation and history binding must discard the entire typed projection
def ApplyColdPat(Document: CadDocument, PatternValue: ColdPatPart) -> CadDocument:
    try:
        Projected = ApplyTiltDoc(
            ReplaceValue(Document, bodies=PatternValue.BodiesValue),
            PatternValue.LinkValue,
            PatternValue.OwnerValue.DatumValue,
        )
        Projected = ApplyPatDoc(
            Projected,
            PatternValue.LinkValue,
            PatternValue.OwnerValue,
            PatternValue.LookValue,
        )
        Result = ApplyPatStock(Projected, PatternValue)
        Result.assert_valid()
        return Result
    except (ValueError, TypeError, KeyError, OverflowError) as ErrorInfo:
        raise ColdPatError() from ErrorInfo
