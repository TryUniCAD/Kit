from convert.adapters.solidworks.Archive.Partition.ReadXmtVector import ReadXmtVector
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.SwReadGraph import (
    SwReadGraph,
)


# stored surface values must be the exact current metre drivers in their signed principal placement
def CheckSwTorus(GraphValue: SwReadGraph, TorusValue: XmtNode) -> None:
    MajorValue, MinorValue = (
        GraphValue.PathValue.CurveValue.Radius,
        GraphValue.SectionValue.CurveValue.Radius,
    )
    if (
        not 0.0 < MinorValue < MajorValue
        or TorusValue.FieldsValue["major_radius"] != MajorValue
        or TorusValue.FieldsValue["minor_radius"] != MinorValue
        or TorusValue.String("sense") != "+"
        or ReadXmtVector(TorusValue, "centre") != (0.0, MajorValue, 0.0)
        or ReadXmtVector(TorusValue, "axis") != (0.0, 0.0, 1.0)
        or ReadXmtVector(TorusValue, "x_axis") != (1.0, 0.0, 0.0)
    ):
        raise ValueError(
            "SOLIDWORKS saved sweep torus disagrees with its actual live drivers"
        )
