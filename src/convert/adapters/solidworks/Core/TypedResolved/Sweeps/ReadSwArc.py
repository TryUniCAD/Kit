from math import hypot as HypotValue, pi as PiValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.ReadSwDriver import (
    CheckSwIndex,
)
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.ReadSwRow import ReadSwRow
from interchange.geometry.Models.GeometryCurves import ArcGeometry, CircleGeometry
from interchange.geometry.Models.VectorPlane import PlaneVector


# a contour radius must describe the exact indexed sketch centers and endpoints
def SwArcPoints(SketchValue: ArchiveNode) -> tuple[PlaneVector, ...]:
    FieldsValue = SketchValue.FieldsValue
    RowsValue = NativeRows(FieldsValue.get("points"))
    if FieldsValue.get("npoints") != len(RowsValue) or any(
        RowValue.get("kind") != 0 for RowValue in RowsValue
    ):
        raise ValueError("SOLIDWORKS sweep has alternate sketch point ownership")
    Positions = tuple(
        NativeRecord(NativeRecord(RowValue.get("point")).get("pos"))
        for RowValue in RowsValue
    )
    return tuple(
        PlaneVector(RequireScalar(Value["x"]), RequireScalar(Value["y"]))
        for Value in Positions
    )


# fixed origin and independent horizontal and vertical participants identify the exact editable path
def CheckSwRules(SketchValue: ArchiveNode, IsSection: bool) -> None:
    DimsValue = NativeRecord(SketchValue.FieldsValue.get("dims"))
    FixedValue = NativeRecord(ReadSwRow(DimsValue, "nlog1", "log_g1", "d"))
    BinaryRows = NativeRows(DimsValue.get("log_g2"))
    Expected = () if IsSection else ((26, 0, 1), (25, 2, 0))
    if (
        FixedValue.get("f80") != 17
        or DimsValue.get("nlog2") != len(BinaryRows)
        or len(BinaryRows) != len(Expected)
        or DimsValue.get("nlog3") != 0
    ):
        raise ValueError(
            "SOLIDWORKS sweep does not retain its fixed and orthogonal relations"
        )
    CheckSwIndex(FixedValue.get("h1"), "sgPointHandle", 0 if IsSection else 1)
    for RowValue, (Relation, FirstIndex, SecondIndex) in zip(
        BinaryRows, Expected, strict=True
    ):
        FieldsValue = NativeRecord(RowValue.get("d"))
        if FieldsValue.get("f80") != Relation:
            raise ValueError("SOLIDWORKS sweep has an alternate path relation")
        CheckSwIndex(FieldsValue.get("h1"), "sgPointHandle", FirstIndex)
        CheckSwIndex(FieldsValue.get("h2"), "sgPointHandle", SecondIndex)


# the full section has one oriented seam while the path has two distinct ordered endpoints
def ReadSwArc(
    SketchValue: ArchiveNode,
    RadiusValue: float,
    IsSection: bool,
) -> CircleGeometry | ArcGeometry:
    FieldsValue = SketchValue.FieldsValue
    ArcValue = NativeRecord(ReadSwRow(FieldsValue, "narcs", "arcs", "arc"))
    if (
        ReadSwRow(FieldsValue, "narcs", "arcs", "flags") != 0
        or ArcValue.get("f08") != 1
        or ArcValue.get("ext") is not None
        or ArcValue.get("group") is not None
        or ArcValue.get("f50") != 0
    ):
        raise ValueError("SOLIDWORKS saved sweep has a foreign or construction profile")
    OriginValue = PlaneVector(0.0, 0.0)
    ExpectedPoints = (
        (OriginValue, PlaneVector(RadiusValue, 0.0))
        if IsSection
        else (
            PlaneVector(0.0, RadiusValue),
            OriginValue,
            PlaneVector(RadiusValue, RadiusValue),
        )
    )
    if any(
        FieldsValue.get(NameValue) != 0
        for NameValue in ("nlines", "nellipses", "nsplines")
    ) or tuple(
        ArcValue.get(NameValue) for NameValue in ("fd8", "fdc_s", "fc8_s", "fcc_s")
    ) != (
        1,
        0,
        1,
        1 if IsSection else 2,
    ):
        raise ValueError(
            "SOLIDWORKS sweep arc disagrees with its ordered driver incidence"
        )
    PointsValue = SwArcPoints(SketchValue)
    if IsSection:
        CenterValue, SeamValue = PointsValue
        if (
            CenterValue != OriginValue
            or HypotValue(SeamValue.x, SeamValue.y) != RadiusValue
        ):
            raise ValueError(
                "SOLIDWORKS saved sweep section seam is off its owned circle"
            )
    elif PointsValue != ExpectedPoints:
        raise ValueError(
            "SOLIDWORKS sweep arc disagrees with its ordered driver incidence"
        )
    CheckSwRules(SketchValue, IsSection)
    if IsSection:
        return CircleGeometry(OriginValue, RadiusValue)
    return ArcGeometry(ExpectedPoints[0], RadiusValue, -PiValue / 2.0, 0.0)
