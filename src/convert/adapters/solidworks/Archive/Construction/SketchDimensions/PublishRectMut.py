from collections import Counter

from convert.adapters.solidworks.Archive.Construction.Dimensions.DimensionGraph import (
    DimensionGraph,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Profile.ProfileGraph import (
    ProfileGraph,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.RequireDimRows import (
    RequireDimRows,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# one final publication must derive constraint counts group ordering and annotation counters from the actual completed graph
def PublishRectMut(
    GraphValue: ProfileGraph,
    ResultValues: tuple[DimensionGraph, ...],
    LogicalValues: tuple[dict[str, object], ...],
    Allocator: PersistentIds,
    AnnotationId: int,
) -> None:
    GeometryValue = GraphValue.GeometryValue
    FieldsValue = RequireDimRows(GeometryValue.SketchValue)
    CountsValue: Counter[ArchiveNode] = Counter()
    for LogicalValue in LogicalValues:
        HandleValue = ArchiveNode.RequireNode(LogicalValue["h1"])
        CountsValue[ArchiveNode.RequireNode(HandleValue.FieldsValue["_line"])] += 1
    for ResultValue in ResultValues:
        for FieldName in ("h1", "h2"):
            HandleValue = ArchiveNode.RequireNode(
                ResultValue.DimensionValue.FieldsValue[FieldName]
            )
            CountsValue[ArchiveNode.RequireNode(HandleValue.FieldsValue["_point"])] += 1
    for ResultValue in ResultValues:
        _ = Allocator.AllocateMut(ResultValue.DimensionValue, "f50")
    for EntityValue in (*GeometryValue.PointValues, *GeometryValue.LineValues):
        EntityValue.FieldsValue["f20"] = CountsValue[EntityValue]
    FieldsValue["log_g1"] = tuple({"d": LogicalValue} for LogicalValue in LogicalValues)
    FieldsValue["nlog1"] = len(LogicalValues)
    FieldsValue["val_g2"] = tuple(
        {"d": ResultValue.DimensionValue} for ResultValue in ResultValues
    )
    FieldsValue["ng2"] = len(ResultValues)
    DisplayList = ArchiveNode.RequireNode(FieldsValue["f118"])
    DisplayList.FieldsValue["items"] = tuple(
        {"o": ResultValue.DisplayValue} for ResultValue in ResultValues
    )
    DisplayList.FieldsValue["n"] = len(ResultValues)
    ModelValue = ArchiveNode.RequireNode(GraphValue.ProfileValue.FieldsValue["owner"])
    ModelValue.FieldsValue["fd44"] = AnnotationId + len(ResultValues)
