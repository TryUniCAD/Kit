from convert.adapters.solidworks.Core.TypedResolved.Revolves.SelectedCut.RevCutBand import RevCutBand
from convert.adapters.solidworks.Core.TypedResolved.Revolves.SelectedCut.RevFaceRef import RevFaceRef


# stock surface references must cover its actual annular meridian without importing another feature
def CheckRevStock(
    Choices: tuple[tuple[RevFaceRef, ...], tuple[RevFaceRef, ...]], FeatureId: int, StockBand: RevCutBand,
) -> None:
    First, Second = Choices
    if (
        any(Value.FeatureId != FeatureId or Value.IsEnd for Value in (*First, *Second))
        or any(len({Value.MarkValue for Value in FaceValue}) != 3 for FaceValue in Choices)
        or {Value.MarkValue for Value in (*First, *Second)} != StockBand.Marks
    ):
        raise ValueError("revolve stock chooser does not cover the actual producer meridian")
