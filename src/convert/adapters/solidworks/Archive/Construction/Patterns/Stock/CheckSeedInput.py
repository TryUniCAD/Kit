from ntpath import basename as BaseName, splitext as SplitExt

from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.FrontStockBox import (
    FrontStockBox,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.SeedStockInput import (
    SeedStockInput,
)


# provisional stock construction must start from actual part and feature identifiers
def CheckSeedInput(InputValue: SeedStockInput) -> tuple[str, str, str, str]:
    if (
        type(InputValue) is not SeedStockInput
        or type(InputValue.PlateValue) is not FrontStockBox
        or type(InputValue.SeedValue) is not FrontStockBox
    ):
        raise ValueError("expected the modeled Front plate and raised seed")
    NamesValue = (
        InputValue.PlateValue.SketchName,
        InputValue.PlateValue.FeatureName,
        InputValue.SeedValue.SketchName,
        InputValue.SeedValue.FeatureName,
    )
    if (
        not all(
            type(Label) is str and Label and Label.isprintable()
            for Label in (InputValue.NameValue, InputValue.ConfigName, *NamesValue)
        )
        or type(InputValue.PathValue) is not str
        or SplitExt(BaseName(InputValue.PathValue)) != (InputValue.NameValue, ".SLDPRT")
        or type(InputValue.SavedAt) is not int
        or not 0 < InputValue.SavedAt < 0x7FFFFFFF
    ):
        raise ValueError(
            "raised seed needs explicit part, profile, operation and lifecycle identities"
        )
    return NamesValue
