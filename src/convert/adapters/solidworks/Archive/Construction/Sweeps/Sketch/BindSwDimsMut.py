from convert.adapters.solidworks.Archive.Construction.Dimensions.DimensionGraph import (
    DimensionGraph,
)
from convert.adapters.solidworks.Archive.Construction.Origin.MakeOriginFix import (
    MakeOriginFix,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakeBinaryDim import (
    MakeBinaryDim,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakePointRef import (
    MakePointRef,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.RequireDimRows import (
    RequireDimRows,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# the path start is fixed to origin while its centre and end retain separate vertical and horizontal relations
def BindSwDimsMut(
    SketchValue: ArchiveNode,
    ArcValue: ArchiveNode,
    PointValues: tuple[ArchiveNode, ArchiveNode, ArchiveNode],
    DriverValue: DimensionGraph,
) -> None:
    MembersValue = RequireDimRows(SketchValue)
    CenterRef, StartRef, EndRef = (
        MakePointRef(SketchValue, PointValues, PointValue) for PointValue in PointValues
    )
    FixedValue = MakeOriginFix(SketchValue, PointValues[1])
    FixedValue.FieldsValue["h1"] = StartRef
    VerticalValue = MakeBinaryDim(
        SketchValue,
        26,
        CenterRef,
        MakePointRef(SketchValue, PointValues, PointValues[1]),
    )
    HorizontalValue = MakeBinaryDim(
        SketchValue, 25, EndRef, MakePointRef(SketchValue, PointValues, PointValues[0])
    )
    FixedRows = ({"d": FixedValue.FieldsValue},)
    RelationRows = ({"d": VerticalValue}, {"d": HorizontalValue})
    DriverRows = ({"d": DriverValue.DimensionValue},)
    DisplayRows = ({"o": DriverValue.DisplayValue},)
    MembersValue.update(
        nlog1=len(FixedRows),
        log_g1=FixedRows,
        nlog2=len(RelationRows),
        log_g2=RelationRows,
        ng1=len(DriverRows),
        val_g1=DriverRows,
    )
    ArchiveNode.RequireNode(MembersValue["f118"]).FieldsValue.update(
        n=len(DisplayRows), items=DisplayRows
    )
    HandlesValue = (
        StartRef,
        *(
            ArchiveNode.RequireNode(Relation[KeyName])
            for Relation in (VerticalValue, HorizontalValue)
            for KeyName in ("h1", "h2")
        ),
    )
    for PointValue in PointValues:
        PointValue.FieldsValue["f20"] = sum(
            HandleValue.FieldsValue["_point"] is PointValue
            for HandleValue in HandlesValue
        )
    ArcValue.FieldsValue["f20"] = len(DriverRows)
