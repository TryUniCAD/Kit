from convert.adapters.solidworks.Archive.Construction.Circles.CircleGraph import (
    CircleGraph,
)
from convert.adapters.solidworks.Archive.Construction.Circles.CircleInput import (
    CircleInput,
)
from convert.adapters.solidworks.Archive.Construction.Profile.ProfileGraph import (
    ProfileGraph,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Bounds.Circles.CheckCircRows import (
    CheckCircRows,
)
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import RequireRecord


# a copied plan or stale radial extent cannot replace the actual circle point and arc aliases in its owned sketch
def CheckCircGeom(ProfileValue: ProfileGraph, CircleValue: CircleInput) -> None:
    Geometry = ProfileValue.GeometryValue
    if type(Geometry) is not CircleGraph:
        raise ValueError("circle bounds require actual circular sketch geometry")
    CheckCircRows(Geometry)
    SketchValue = Geometry.SketchValue
    ArcValue = Geometry.ArcValue
    Center = RequireRecord(Geometry.CenterValue.FieldsValue.get("pos"))
    Marker = RequireRecord(Geometry.MarkerValue.FieldsValue.get("pos"))
    CenterX, CenterY = CircleValue.CenterValue
    MarkerX, MarkerY = CircleValue.MarkerValue
    if (
        ProfileValue.ProfileValue.FieldsValue.get("pd_f80") is not SketchValue
        or SketchValue.FieldsValue.get("f138") is not ProfileValue.ProfileValue
        or ArcValue.FieldsValue.get("_sketch") is not SketchValue
        or ArcValue.FieldsValue.get("_center") is not Geometry.CenterValue
        or ArcValue.FieldsValue.get("_start") is not Geometry.MarkerValue
        or ArcValue.FieldsValue.get("_end") is not Geometry.MarkerValue
        or (Center.get("x"), Center.get("y")) != (CenterX, CenterY)
        or (Marker.get("x"), Marker.get("y")) != (MarkerX, MarkerY)
        or SketchValue.FieldsValue.get("narcs") != 1
        or SketchValue.FieldsValue.get("npoints") != 2
    ):
        raise ValueError("circle bounds plan differs from its actual radial geometry")
