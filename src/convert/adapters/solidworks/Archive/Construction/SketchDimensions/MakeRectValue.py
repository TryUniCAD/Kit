from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeLengthParam import (
    MakeLengthParam,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakePoint import (
    MakePoint,
)
from convert.adapters.solidworks.Archive.Construction.Profile.ProfileGraph import (
    ProfileGraph,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.DimBaseFields import (
    DimBaseFields,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakePointRef import (
    MakePointRef,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# each fresh length driver must own its named parameter and two actual point references before persistent allocation
def MakeRectValue(
    GraphValue: ProfileGraph, IndexValue: int, LengthValue: float, NameValue: str
) -> ArchiveNode:
    GeometryValue = GraphValue.GeometryValue
    Parameter = MakeLengthParam(GraphValue.ProfileValue, LengthValue, NameValue)
    FieldsValue = DimBaseFields()
    FieldsValue.update(
        {
            "owner": GraphValue.ProfileValue,
            "_sketch": GeometryValue.SketchValue,
            "f28": Parameter,
            "f80": 1,
            "f90": 2,
            "f94": 0,
            "f98": 0,
            "fa0": 0,
            "h1": MakePointRef(
                GeometryValue.SketchValue,
                GeometryValue.PointValues,
                GeometryValue.PointValues[IndexValue],
            ),
            "h2": MakePointRef(
                GeometryValue.SketchValue,
                GeometryValue.PointValues,
                GeometryValue.PointValues[IndexValue + 1],
            ),
            "f180": 1,
            "f184": 1,
            "f1b8": 1,
            "f1bc": 0,
            "plane": None,
            "dir": MakePoint(),
        }
    )
    return ArchiveNode(RuntimeClass("sgPntPntDist", 1), FieldsValue)
