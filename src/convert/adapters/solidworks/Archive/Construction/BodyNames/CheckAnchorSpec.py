from convert.adapters.solidworks.Archive.Construction.BodyNames.AnchorPartInput import (
    AnchorPartInput,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.RectDimInput import (
    RectDimInput,
)


# an explicit supported anchor request must be verified before new native ownership is allocated
def CheckAnchorSpec(InputValue: AnchorPartInput) -> None:
    if (
        type(InputValue) is not AnchorPartInput
        or InputValue.KindValue not in ("corner", "center")
        or type(InputValue.DimensionsValue) is not RectDimInput
    ):
        raise ValueError("anchored part requires its complete declared anchor input")
