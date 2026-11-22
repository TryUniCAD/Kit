from math import atan2 as ArcTangent, degrees as Degrees, hypot as Hypot
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Core.Native import NativeProfile
from convert.adapters.solidworks.Core.TypedResolved.CirclePointIndex import (
    FindCirclePoint,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows


# a normal closed circle must follow its actual endpoint and centre identities
def ReadCircleShape(
    SketchValue: ArchiveNode,
) -> tuple[NativeProfile, int, tuple[float, float]] | None:
    FieldsValue = SketchValue.FieldsValue
    ArcsValue = NativeRows(FieldsValue.get("arcs"))
    if len(ArcsValue) != 1 or any(
        FieldsValue.get(NameValue)
        for NameValue in ("lines", "ellipses", "parabolas", "splines")
    ):
        return None
    ArcValue = NativeRecord(ArcsValue[0].get("arc"))
    if (
        ArcsValue[0].get("flags") != 0
        or ArcValue.get("ext") is not None
        or ArcValue.get("f08") != 1
        or ArcValue.get("fd0") != 1
        or CastValue(int, ArcValue.get("f54")) & 1
    ):
        return None
    StartValue = FindCirclePoint(ArcValue, "fc8")
    EndValue = FindCirclePoint(ArcValue, "fcc")
    CenterValue = FindCirclePoint(ArcValue, "fdc")
    Points = NativeRows(FieldsValue.get("points"))
    if (
        len(Points) != 2
        or StartValue != EndValue
        or {StartValue, CenterValue} != {0, 1}
    ):
        return None
    Center = NativeRecord(NativeRecord(Points[CenterValue].get("point")).get("pos"))
    SeamValue = NativeRecord(NativeRecord(Points[StartValue].get("point")).get("pos"))
    XValue, YValue = RequireScalar(Center.get("x")), RequireScalar(Center.get("y"))
    DeltaX = RequireScalar(SeamValue.get("x")) - XValue
    DeltaY = RequireScalar(SeamValue.get("y")) - YValue
    Radius = Hypot(DeltaX, DeltaY)
    if Radius <= 0.0:
        return None
    return (
        NativeProfile(
            "circle",
            (1000.0 * XValue, 1000.0 * YValue, 1000.0 * Radius),
            (),
            start_angle_degrees=Degrees(ArcTangent(DeltaY, DeltaX)),
        ),
        CenterValue,
        (XValue, YValue),
    )
