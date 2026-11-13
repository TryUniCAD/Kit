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
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.WallFace import WallFace
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PlaneSpan import KPlaneSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSolid import (
    PrismSolid,
)


def CapTagSet(
    Solids: tuple[PrismSolid, ...], Index: int, IsRoof: bool
) -> tuple[int, int, int]:
    Ledger = TagLedger()
    Found = (-1, -1)
    for Ordinal, Solid in enumerate(Solids[: Index + 1]):
        Shape = BuildShape(Solid)
        FaceTags, BodyTag = LedgerTags((Shape,), Ledger)[0]
        if Ordinal != Index:
            continue
        Level = Solid.Slabs[-1].UpperCm if IsRoof else Solid.Slabs[0].LowerCm
        Covers = [
            FaceValue
            for FaceValue in Shape.Faces
            if isinstance(FaceValue, CapFace)
            and FaceValue.Upward == IsRoof
            and FaceValue.LevelCm == Level
        ]
        if len(Covers) != 1:
            raise ValueError("Fusion part feature requires one roof or base face")
        Found = (FaceTags[FaceKey(Covers[0])], BodyTag)
    return Found[0], Found[1], Ledger.NextTag


def RoofTagSet(Solids: tuple[PrismSolid, ...], Index: int) -> tuple[int, int, int]:
    return CapTagSet(Solids, Index, True)


def RoofTag(Solids: tuple[PrismSolid, ...], Index: int) -> int:
    return RoofTagSet(Solids, Index)[0]


def SideTags(
    Solids: tuple[PrismSolid, ...], Index: int, Spans: tuple[KPlaneSpan, ...]
) -> tuple[int, ...]:
    Ledger = TagLedger()
    Found: dict[KPlaneSpan, int] = {}
    for Ordinal, Solid in enumerate(Solids[: Index + 1]):
        Shape = BuildShape(Solid)
        FaceTags = LedgerTags((Shape,), Ledger)[0][0]
        if Ordinal != Index:
            continue
        Found = {
            FaceValue.Span: FaceTags[FaceKey(FaceValue)]
            for FaceValue in Shape.Faces
            if isinstance(FaceValue, WallFace)
        }
    if any(SpanValue not in Found for SpanValue in Spans):
        raise ValueError("Fusion part shell sides require whole side faces")
    return tuple(Found[SpanValue] for SpanValue in Spans)
