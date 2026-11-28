from convert.adapters.solidworks.Archive.Construction.Dimensions.DimensionGraph import (
    DimensionGraph,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordDim import (
    KeywordDim,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeKeyDisplay import (
    KKeyLengthScale,
    MakeKeyDisplay,
)
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName


# editable sketch keyword dimensions must project their real parameter names and lengths in the actual document presentation units
def MakeSketchKeys(
    ResultValues: tuple[DimensionGraph, ...], UnitText: str
) -> tuple[KeywordDim, ...]:
    _ = KKeyLengthScale[UnitText]
    return tuple(
        MakeKeyDisplay(
            ReadNodeName(ResultValue.ParameterValue),
            RequireScalar(ResultValue.ParameterValue.FieldsValue["f58"]),
            UnitText,
        )
        for ResultValue in ResultValues
    )
