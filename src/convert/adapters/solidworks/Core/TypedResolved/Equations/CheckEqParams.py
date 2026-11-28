from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.DepthOwner import DepthOwner
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.LineDriver import (
    LineDriver,
)


# published parameter ids are safe only when both exact live archive owners are present and unique
def CheckEqParams(
    Model: NativeModel,
    SketchId: int,
    BossId: int,
    WidthValue: LineDriver,
    DepthValue: DepthOwner,
    *,
    HeightValue: LineDriver | None = None,
) -> None:
    Features = {Feature.object_id: Feature for Feature in Model.features}
    WidthRows = tuple(
        Dimension
        for Dimension in Features[SketchId].dimensions
        if Dimension.name == WidthValue.NameValue
    )
    DepthRows = tuple(
        Dimension
        for Dimension in Features[BossId].dimensions
        if Dimension.name == DepthValue.DepthValue.name
    )
    if (
        len(WidthRows) != 1
        or len(DepthRows) != 1
        or WidthRows[0].TypedOwner.get("object_index")
        != WidthValue.ParamValue.IndexValue
        or DepthRows[0] != DepthValue.DepthValue
    ):
        raise ValueError(
            "local width-depth equation lacks its exact public parameter owners"
        )

    if HeightValue is not None and (
        len(Features[SketchId].dimensions) != 2
        or Features[BossId].dimensions != (DepthValue.DepthValue,)
        or not any(
            Dimension.name == HeightValue.NameValue
            and Dimension.TypedOwner.get("object_index")
            == HeightValue.ParamValue.IndexValue
            for Dimension in Features[SketchId].dimensions
        )
    ):
        raise ValueError("named width-depth equation has unbound public dimensions")
