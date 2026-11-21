from convert.adapters.solidworks.Core.TypedResolved.Revolves.SelectedCut.RevFaceRef import (
    RevFaceRef,
)


# each result face carries one actual stock wall and three owned cut surfaces and a distinct angular cap
def CheckRevResult(
    Choices: tuple[tuple[RevFaceRef, ...], tuple[RevFaceRef, ...]],
    StockId: int,
    CutId: int,
    WallMark: int,
    CutMarks: frozenset[int],
) -> None:
    for CapIndex, Faces in enumerate(Choices):
        Expected = {(CutId, True, CapIndex), (StockId, False, WallMark)} | {
            (CutId, False, MarkValue) for MarkValue in CutMarks
        }
        if (
            len(Faces) != 5
            or {(Value.FeatureId, Value.IsEnd, Value.MarkValue) for Value in Faces}
            != Expected
        ):
            raise ValueError(
                "revolve cut result chooser crosses the selected wall or actual cut ends"
            )
