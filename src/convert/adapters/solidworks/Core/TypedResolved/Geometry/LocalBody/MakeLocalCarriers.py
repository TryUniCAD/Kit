from dataclasses import replace as Replace
from math import isfinite as IsFinite

from convert.Geometry.Parasolid import AnalyticGeom, NativeId, RecordTables
from convert.adapters.solidworks.Archive.Partition.ReadXmtVector import ReadXmtVector
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from interchange.brep.Curves.BrepCurves import LineCurve
from interchange.brep.Surfaces.BrepSurfaces import PlaneSurface
from interchange.Core.Common import FreezeMapping


# analytic carriers reuse the neutral geometry constructor from their typed coordinates
def AddLocalGeomMut(TablesValue: RecordTables, NodeValue: XmtNode) -> None:
    IsCurve = NodeValue.KindValue == 30
    FieldNames = ("pvec", "direction") if IsCurve else ("pvec", "normal", "x_axis")
    Values = tuple(
        Component
        for FieldName in FieldNames
        for Component in ReadXmtVector(NodeValue, FieldName)
    )
    if any(not IsFinite(Component) or abs(Component) > 1000000 for Component in Values):
        raise ValueError("local analytic carrier has invalid coordinates")
    IndexValue = NodeValue.IndexValue + 1
    Carrier = AnalyticGeom(
        NodeValue.KindValue,
        NativeId("curve" if IsCurve else "surface", IndexValue),
        Values,
    )
    if NodeValue.String("sense") not in {"+", "-"} or not isinstance(
        Carrier, (LineCurve, PlaneSurface)
    ):
        raise ValueError("local body has an unsupported analytic carrier")
    Attributes = FreezeMapping(
        {
            "sense": NodeValue.String("sense") == "+",
            "header_references": tuple(
                NodeValue.Integer(FieldName) + 1
                for FieldName in ("attributes_features", "owner", "previous", "next")
            ),
        }
    )
    if isinstance(Carrier, LineCurve):
        TablesValue.curves[IndexValue] = Replace(Carrier, attributes=Attributes)
    else:
        TablesValue.surfaces[IndexValue] = Replace(Carrier, attributes=Attributes)
