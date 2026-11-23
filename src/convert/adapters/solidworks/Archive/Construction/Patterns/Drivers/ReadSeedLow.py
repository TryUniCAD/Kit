from convert.adapters.solidworks.Archive.Construction.Datums.Angles.DatumVector import (
    KDatumVector,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.SeedStockGraph import (
    SeedStockGraph,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.PolygonGraph import (
    PolygonGraph,
)
from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import (
    PrincipalFrame,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    ReadRows,
    RequireNode,
    RequireRecord,
)


# the first pitch witness belongs to the actual local seed contour
def ReadSeedLow(
    StockValue: SeedStockGraph, PatternValue: ArchiveNode
) -> tuple[KDatumVector, KDatumVector]:
    SeedValue = StockValue.SeedValue
    ItemsValue = RequireNode(PatternValue.FieldsValue.get("f988"), "suObList")
    RowsValue = ReadRows(ItemsValue.FieldsValue.get("items"))
    ProfileValue = SeedValue.ProfileValue
    Geometry = ProfileValue.GeometryValue
    if (
        ItemsValue.FieldsValue.get("n") != 1
        or len(RowsValue) != 1
        or RowsValue[0].get("o") is not SeedValue.FeatureValue
        or ProfileValue.FrameValue != PrincipalFrame("z")
        or not isinstance(Geometry, PolygonGraph)
        or Geometry.SketchValue
        is not ProfileValue.ProfileValue.FieldsValue.get("pd_f80")
        or len(Geometry.PointValues) != 4
    ):
        raise ValueError(
            "principal pattern pitch requires its actual rectangular Front seed"
        )
    Points = tuple(
        RequireRecord(NodeValue.FieldsValue.get("pos"))
        for NodeValue in Geometry.PointValues
    )
    First = tuple(RequireScalar(Points[0].get(KeyValue)) for KeyValue in ("x", "y"))
    if any(
        First[Index]
        != min(RequireScalar(PointValue.get(KeyValue)) for PointValue in Points)
        for Index, KeyValue in enumerate(("x", "y"))
    ):
        raise ValueError("principal pattern pitch requires the seed lower corner first")
    FrameValue = ProfileValue.FrameValue
    return (First[0], First[1], FrameValue.OriginValue[2]), FrameValue.NormalValue
