from convert.adapters.solidworks.Archive.Construction.Dimensions.DimensionGraph import (
    DimensionGraph,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    ReadRows,
    RequireNode,
)


# circle bounds require every live end display to retain its actual owned handle dimension and unextended scalar parameter
def CheckCircDim(
    GraphValue: DimensionGraph, OwnerValue: ArchiveNode, IsAngular: bool
) -> float:
    Handle = RequireNode(GraphValue.HandleValue, "moFeatureDimHandle_c")
    Dimension = RequireNode(
        GraphValue.DimensionValue,
        "AngleDim_c" if IsAngular else "ParallelPlaneDistanceDim_c",
    )
    Parameter = RequireNode(
        GraphValue.ParameterValue,
        "moAngleParameter_c" if IsAngular else "moLengthParameter_c",
    )
    Display = RequireNode(
        GraphValue.DisplayValue,
        "moDisplayAngularDim_c" if IsAngular else "moDisplayDistanceDim_c",
    )
    Handles = ReadRows(Display.FieldsValue.get("f850"))
    if (
        len(Handles) != 1
        or Handles[0].get("o") is not Handle
        or Handle.FieldsValue.get("owner") is not OwnerValue
        or Handle.FieldsValue.get("ff0") is not Dimension
        or Dimension.FieldsValue.get("owner") is not OwnerValue
        or Dimension.FieldsValue.get("f28") is not Parameter
        or any(
            Handle.FieldsValue.get(NameValue) is not None
            for NameValue in ("fe8", "f100")
        )
        or Parameter.FieldsValue.get("f48") is not None
        or any(
            Parameter.FieldsValue.get(NameValue) != 0
            for NameValue in ("f68", "f0c", "f2c")
        )
        or any(
            Dimension.FieldsValue.get(NameValue) is not None
            for NameValue in ("f48", "f60")
        )
        or any(
            Dimension.FieldsValue.get(NameValue) != 0
            for NameValue in ("f54", "f5c", "f68", "has_f78")
        )
    ):
        raise ValueError(
            "circle bounds end dimension lost its actual local scalar owner"
        )
    return RequireScalar(Parameter.FieldsValue.get("f58"))


# inactive end values and draft controls must preserve the same bounded ordinary circle semantics as its typed reader
def CheckCircDims(ChildValue: PartCandidate) -> None:
    BossValue = ChildValue.BossValue
    GraphValues = BossValue.DimensionsValue
    Values = tuple(
        CheckCircDim(GraphValue, BossValue.FeatureValue, IndexValue >= 2)
        for IndexValue, GraphValue in enumerate(GraphValues)
    )
    if (
        len(GraphValues) != 4
        or len({id(Value.DimensionValue) for Value in GraphValues}) != 4
        or len({id(Value.ParameterValue) for Value in GraphValues}) != 4
        or Values
        != (ChildValue.PlanValue.DepthValue, ChildValue.PlanValue.DepthValue, 0.0, 0.0)
        or CheckCircDim(BossValue.FromValue, BossValue.FeatureValue, False) != 0.0
    ):
        raise ValueError(
            "circle bounds require matching depths and inactive draft values"
        )
