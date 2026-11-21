from dataclasses import replace as Replace
from math import isfinite as IsFinite

from convert.Geometry.Parasolid import AnalyticGeom, NativeId, RecordTables
from convert.adapters.solidworks.Archive.Partition.ReadXmtVector import ReadXmtVector
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from interchange.brep.Curves.BrepCurves import CircleCurve
from interchange.brep.Surfaces.BrepSurfaces import CylinderSurface
from interchange.Core.Common import FreezeMapping


# periodic carriers need the shared analytic unit conversion and exact native references
def AddCylGeomMut(TablesValue: RecordTables, NodeValue: XmtNode) -> None:
    IndexValue = NodeValue.IndexValue + 1
    KindValue = NodeValue.KindValue
    RadiusValue = NodeValue.FieldsValue["radius"]
    if type(RadiusValue) is not float:
        raise ValueError("local cylinder carrier has no radius")
    if KindValue == 31:
        RoleValue = "curve"
        Values = (
            *ReadXmtVector(NodeValue, "centre"),
            *ReadXmtVector(NodeValue, "normal"),
            *ReadXmtVector(NodeValue, "x_axis"),
            RadiusValue,
        )
    else:
        RoleValue = "surface"
        Values = (
            *ReadXmtVector(NodeValue, "pvec"),
            *ReadXmtVector(NodeValue, "axis"),
            RadiusValue,
            *ReadXmtVector(NodeValue, "x_axis"),
        )
    if any(not IsFinite(Component) or abs(Component) > 1000000 for Component in Values):
        raise ValueError("local cylinder carrier has invalid coordinates")
    Carrier = AnalyticGeom(KindValue, NativeId(RoleValue, IndexValue), Values)
    Attributes = FreezeMapping(
        {
            "sense": NodeValue.String("sense") == "+",
            "header_references": tuple(
                NodeValue.Integer(FieldName) + 1
                for FieldName in ("attributes_features", "owner", "previous", "next")
            ),
        }
    )
    if isinstance(Carrier, CircleCurve):
        TablesValue.curves[IndexValue] = Replace(Carrier, attributes=Attributes)
    elif isinstance(Carrier, CylinderSurface):
        TablesValue.surfaces[IndexValue] = Replace(Carrier, attributes=Attributes)
    else:
        raise ValueError("local body has an unqualified periodic carrier")
