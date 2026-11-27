from convert.adapters.solidworks.Archive.Construction.Styles.MakeCharFormat import (
    MakeCharFormat,
)


# explicit style construction preserves native field ownership without loading preferences resources or saved document state
def MakeHelperFont(*, FontName: str) -> dict[str, object]:
    return MakeCharFormat(
        FontName=FontName, HeightValue=-1, PointHeight=0, LineSpacing=0.001
    )
