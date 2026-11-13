from convert.formats.Fusion.DocumentCodec.PartFeatures.History.TagLedger import (
    TagLedger,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeBody import ShapeBody


def LedgerTags(
    Bodies: tuple[ShapeBody, ...], Ledger: TagLedger
) -> list[tuple[dict[tuple[object, ...], int], int]]:
    BodyTags = [Ledger.Claim(("body", Ordinal)) for Ordinal in range(len(Bodies))]
    return [
        (Ledger.FaceTags(BodyValue, Ordinal), BodyTags[Ordinal])
        for Ordinal, BodyValue in enumerate(Bodies)
    ]
