from convert.adapters.solidworks.Archive.Construction.Circles.MakeArcHandle import (
    MakeArcHandle,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeLengthParam import (
    MakeLengthParam,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakePoint import (
    MakePoint,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.DimBaseFields import (
    DimBaseFields,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import RequireRecord


# the live radial dimension reads the actual arc incidence and owns the local arc handle
def MakePathParam(
    ProfileValue: ArchiveNode,
    SketchValue: ArchiveNode,
    ArcValue: ArchiveNode,
    PointValues: tuple[ArchiveNode, ArchiveNode, ArchiveNode],
) -> tuple[ArchiveNode, ArchiveNode]:
    CenterValue, StartValue, EndValue = PointValues
    PositionValue = RequireRecord(CenterValue.FieldsValue["pos"])
    RadiusValue = RequireScalar(PositionValue["y"])
    if (
        len(set(PointValues)) != 3
        or any(
            ArcValue.FieldsValue[NameValue] is not OwnerValue
            for NameValue, OwnerValue in (
                ("_sketch", SketchValue),
                ("_center", CenterValue),
                ("_start", StartValue),
                ("_end", EndValue),
            )
        )
        or PositionValue["x"] != 0.0
        or StartValue.FieldsValue["pos"] != {"x": 0.0, "y": 0.0}
        or EndValue.FieldsValue["pos"] != {"x": RadiusValue, "y": RadiusValue}
    ):
        raise ValueError(
            "sweep radial driver requires the actual signed quarter arc incidence"
        )
    ParameterValue = MakeLengthParam(ProfileValue, RadiusValue)
    UnsetHandle = ArchiveNode(
        RuntimeClass("sgEntHandle", 1),
        {"_sketch": None, "idx": 0x777F, "f18": -2, "f1c": -1, "f08": 0},
    )
    return ParameterValue, ArchiveNode(
        RuntimeClass("sgCircleDim", 1),
        {
            **DimBaseFields(),
            "owner": ProfileValue,
            "_sketch": SketchValue,
            "f28": ParameterValue,
            "f80": 3,
            "f90": 2,
            "f94": 0,
            "f98": 0,
            "fa0": 0,
            "g1": 0,
            "g2": 0,
            "dir": MakePoint(XValue=1.0),
            "h1": MakeArcHandle(SketchValue, ArcValue, 0),
            "h2": UnsetHandle,
        },
    )
