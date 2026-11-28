from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Circles.MakeArcHandle import (
    MakeArcHandle,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.FieldRecord import (
    FieldRecord,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.EntityFields import (
    EntityFields,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.MakeRingPoint import (
    MakeRingPoint,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from interchange.geometry.Models.GeometryCurves import ArcGeometry


# a quarter arc requires distinct centre and endpoint nodes with actual local handles and ordinal links
def MakePathArcMut(
    SketchValue: ArchiveNode, PathValue: ArcGeometry
) -> tuple[ArchiveNode, tuple[ArchiveNode, ArchiveNode, ArchiveNode]]:
    CenterValue = MakeRingPoint(
        SketchValue, (PathValue.Center.XCoord, PathValue.Center.YCoord), 2
    )
    StartValue = MakeRingPoint(SketchValue, (0.0, 0.0), 0)
    EndValue = MakeRingPoint(
        SketchValue, (PathValue.Radius, PathValue.Center.YCoord), 1
    )
    PointValues = (CenterValue, StartValue, EndValue)
    FieldsValue = EntityFields(SketchValue)
    FieldsValue.update(
        {
            "_center": CenterValue,
            "_start": StartValue,
            "_end": EndValue,
            "f08": 1,
            "f0c": 1,
            "fd4": 0,
            "seg_tol": -1.0,
            "fd8": 1,
            "fe0": -2,
            "fe4": -2,
            "fe8": -2,
            "fec": -2,
        }
    )
    for NameValue, PointValue in (
        ("fc8", StartValue),
        ("fcc", EndValue),
        ("fdc", CenterValue),
    ):
        FieldsValue[NameValue] = FieldsValue[NameValue + "_s"] = PointValues.index(
            PointValue
        )
    ArcValue = ArchiveNode(RuntimeClass("sgArc", 1), FieldsValue)
    for PointValue in PointValues:
        PointValue.FieldsValue.update(fe8=1, fec=int(PointValue is CenterValue))
    for PointValue in (StartValue, EndValue):
        PointValue.FieldsValue["h1"] = MakeArcHandle(SketchValue, ArcValue, 0)
    FieldsValue["fd0"] = 1
    SketchValue.FieldsValue.update(
        points=tuple(
            {"kind": 0, "point": PointValue.FieldsValue} for PointValue in PointValues
        ),
        arcs=({"flags": 0, "arc": FieldsValue},),
        npoints=len(PointValues),
        narcs=1,
        f130=2,
        f56c=2,
    )
    CreationValue = CastValue(
        dict[str, object], FieldRecord(SketchValue.FieldsValue["f140"])
    )
    CreationValue.update(f08=len(PointValues) + 1, f10=2)
    return ArcValue, PointValues
