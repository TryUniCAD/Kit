from convert.adapters.solidworks.Archive.Construction.Dimensions.DimensionGraph import (
    DimensionGraph,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordDim import (
    KeywordDim,
)
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName


# editable sketch keyword dimensions must project their real parameter names and lengths in the actual document presentation units
def MakeRectKeys(
    ResultValues: tuple[DimensionGraph, ...], UnitText: str
) -> tuple[KeywordDim, ...]:
    ScaleValue = {"mm": 0.001, "m": 1.0, "in": 0.0254}[UnitText]
    return tuple(
        KeywordDim(
            ReadNodeName(ResultValue.ParameterValue),
            RequireScalar(ResultValue.ParameterValue.FieldsValue["f58"]) / ScaleValue,
            None,
        )
        for ResultValue in ResultValues
    )
