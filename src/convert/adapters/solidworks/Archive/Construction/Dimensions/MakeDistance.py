from convert.adapters.solidworks.Archive.Construction.Dimensions.DistanceInput import (
    DistanceInput,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.DimensionGraph import (
    DimensionGraph,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.LinearStyle import (
    LinearStyle,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeHandleMut import (
    MakeHandleMut,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeDimValue import (
    MakeDimValue,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeDistDisplay import (
    MakeDistDisplay,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeLengthParam import (
    MakeLengthParam,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    RequireNode,
)


# live distance construction keeps actual parameter dimension handle and display ownership separate before native ids are allocated
def MakeDistance(
    OwnerValue: ArchiveNode, InputValue: DistanceInput, StyleValue: LinearStyle
) -> DimensionGraph:
    _ = RequireNode(OwnerValue, "moMateDistanceDim_c")
    if FieldInt(OwnerValue.FieldsValue, "f2b0") != 19000:
        raise ValueError("fresh planar distance display requires native version 19000")
    Parameter = MakeLengthParam(OwnerValue, InputValue.ValueMetres)
    Dimension = MakeDimValue(OwnerValue, Parameter)
    HandleValue = MakeHandleMut(OwnerValue, Dimension)
    DisplayValue = MakeDistDisplay(OwnerValue, HandleValue, InputValue, StyleValue)
    return DimensionGraph(Parameter, Dimension, HandleValue, DisplayValue)
