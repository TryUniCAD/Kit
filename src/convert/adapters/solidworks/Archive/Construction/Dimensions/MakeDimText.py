from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeTextFields import (
    MakeTextFields,
)


# existing planar mate callers retain their exact native text kind after the common display text construction is shared
def MakeDimText() -> dict[str, object]:
    return MakeTextFields(18)
