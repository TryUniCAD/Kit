from convert.adapters.solidworks.Archive.Construction.Dimensions.DimensionGraph import (
    DimensionGraph,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.ReadDriverName import (
    ReadDriverName,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.ReadModelLinear import (
    ReadModelLinear,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Profile.ProfileGraph import (
    ProfileGraph,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.CheckRectAlloc import (
    CheckRectAlloc,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakeAxisDim import (
    MakeAxisDim,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakeRectDisplay import (
    MakeRectDisplay,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakeRectValue import (
    MakeRectValue,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakeSketchRef import (
    MakeSketchRef,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.PublishRectMut import (
    PublishRectMut,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.ReadRectDrivers import (
    ReadRectDrivers,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.RectDimInput import (
    RectDimInput,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.RequireDimRows import (
    RequireDimRows,
)
from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import (
    PrincipalFrame,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt


# real editable rectangle lengths require the complete value handle display and unary relation graph before its single owned publication
def MakeRectDimsMut(
    GraphValue: ProfileGraph,
    InputValue: RectDimInput,
    Allocator: PersistentIds,
    DriverNames: tuple[str, str] = ("D1", "D2"),
) -> tuple[DimensionGraph, ...]:
    if type(InputValue) is not RectDimInput:
        raise TypeError(
            "rectangle dimensions require typed explicit presentation inputs"
        )
    NamesValue = tuple(ReadDriverName(NameValue) for NameValue in DriverNames)
    if (
        len(NamesValue) != 2
        or len({NameValue.casefold() for NameValue in NamesValue}) != 2
    ):
        raise ValueError(
            "rectangle sketch requires two distinct driving parameter names"
        )
    Drivers = ReadRectDrivers(GraphValue)
    if GraphValue.FrameValue != PrincipalFrame("z") and (
        any(InputValue.TextDepths) or isinstance(InputValue.RouteCenter, tuple)
    ):
        raise ValueError("spatial rectangle labels require the canonical Front frame")
    CheckRectAlloc(Allocator)
    _ = RequireDimRows(GraphValue.GeometryValue.SketchValue)
    ModelValue = ArchiveNode.RequireNode(GraphValue.ProfileValue.FieldsValue["owner"])
    StyleValue = ReadModelLinear(ModelValue)
    AnnotationId = FieldInt(ModelValue.FieldsValue, "fd44")
    if not 0 < AnnotationId <= 0x7FFFFFFD:
        raise ValueError(
            "model annotation counter cannot allocate both rectangle displays"
        )
    ValueNodes = tuple(
        MakeRectValue(GraphValue, FirstIndex, LastIndex, LengthValue, NameValue)
        for (FirstIndex, LastIndex, LengthValue), NameValue in zip(
            Drivers, NamesValue, strict=True
        )
    )
    ResultValues: list[DimensionGraph] = []
    for IndexValue, (Dimension, Driver) in enumerate(
        zip(ValueNodes, Drivers, strict=True)
    ):
        FirstIndex, LastIndex, LengthValue = Driver
        HandleValue = MakeSketchRef(GraphValue, ValueNodes, IndexValue)
        DisplayValue = MakeRectDisplay(
            GraphValue,
            HandleValue,
            LengthValue,
            IndexValue,
            (FirstIndex, LastIndex),
            AnnotationId + IndexValue,
            InputValue,
            StyleValue,
        )
        ResultValues.append(
            DimensionGraph(
                ArchiveNode.RequireNode(Dimension.FieldsValue["f28"]),
                Dimension,
                HandleValue,
                DisplayValue,
            )
        )
    LogicalValues = tuple(
        MakeAxisDim(GraphValue.GeometryValue, IndexValue) for IndexValue in range(4)
    )
    ResultTuple = tuple(ResultValues)
    PublishRectMut(GraphValue, ResultTuple, LogicalValues, Allocator, AnnotationId)
    return ResultTuple
