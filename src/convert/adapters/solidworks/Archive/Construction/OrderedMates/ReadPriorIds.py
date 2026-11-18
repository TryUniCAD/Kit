from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadRows,
    RequireNode,
)


# prior distance dimensions retain their separate earlier persistent identifier and actual value handle chain while other mate kinds allocate no extra persistent node
def ReadPriorIds(MateValue: ArchiveNode, Allocator: PersistentIds) -> tuple[int, ...]:
    MateId = FieldInt(MateValue.FieldsValue, "f08")
    if Allocator.Allocations.get((MateValue, "f08")) != MateId:
        raise ValueError(
            "ordered prior mate was not allocated by the actual parent allocator"
        )
    if MateValue.ClassValue.NameValue != "moMateDistanceDim_c":
        return (MateId,)
    DisplayValue = RequireNode(
        MateValue.FieldsValue.get("f4b8"), "moDisplayDistanceDim_c"
    )
    HandlesValue = ReadRows(DisplayValue.FieldsValue.get("f850"))
    if len(HandlesValue) != 1:
        raise ValueError(
            "ordered distance requires its one actual retaining display handle"
        )
    HandleValue = RequireNode(HandlesValue[0].get("o"), "moFeatureDimHandle_c")
    Dimension = RequireNode(
        HandleValue.FieldsValue.get("ff0"), "ParallelPlaneDistanceDim_c"
    )
    Parameter = RequireNode(Dimension.FieldsValue.get("f28"), "moLengthParameter_c")
    DimensionId = FieldInt(Dimension.FieldsValue, "f50")
    if not 0 <= DimensionId < MateId or FieldInt(Parameter.FieldsValue, "f08") != -1:
        raise ValueError(
            "ordered distance dimension allocation or parameter identity differs"
        )
    if Allocator.Allocations.get((Dimension, "f50")) != DimensionId:
        raise ValueError(
            "ordered prior dimension was not allocated by the actual parent allocator"
        )
    return DimensionId, MateId
