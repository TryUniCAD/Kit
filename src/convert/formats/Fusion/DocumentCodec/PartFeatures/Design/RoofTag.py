from convert.formats.Fusion.DocumentCodec.PartFeatures.History.FaceKey import FaceKey
from convert.formats.Fusion.DocumentCodec.PartFeatures.History.LedgerTags import (
    LedgerTags,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.History.TagLedger import (
    TagLedger,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.BuildShape import (
    BuildShape,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.CapFace import CapFace
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSolid import (
    PrismSolid,
)


def RoofTagSet(Solids: tuple[PrismSolid, ...], Index: int) -> tuple[int, int, int]:
    Ledger = TagLedger()
    Found = (-1, -1)
    for Ordinal, Solid in enumerate(Solids[: Index + 1]):
        Shape = BuildShape(Solid)
        FaceTags, BodyTag = LedgerTags((Shape,), Ledger)[0]
        if Ordinal != Index:
            continue
        Level = Solid.Slabs[-1].UpperCm
        Roofs = [
            FaceValue
            for FaceValue in Shape.Faces
            if isinstance(FaceValue, CapFace)
            and FaceValue.Upward
            and FaceValue.LevelCm == Level
        ]
        if len(Roofs) != 1:
            raise ValueError("Fusion part feature requires one roof face")
        Found = (FaceTags[FaceKey(Roofs[0])], BodyTag)
    return Found[0], Found[1], Ledger.NextTag


def RoofTag(Solids: tuple[PrismSolid, ...], Index: int) -> int:
    return RoofTagSet(Solids, Index)[0]
