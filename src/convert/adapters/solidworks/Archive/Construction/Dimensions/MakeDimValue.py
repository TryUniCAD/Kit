from convert.adapters.solidworks.Archive.Construction.Dimensions.MakePoint import (
    MakePoint,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# named feature dimensions retain their real parameter and owner before registration allocates their separate persistent identity
def MakeDimValue(OwnerValue: ArchiveNode, Parameter: ArchiveNode) -> ArchiveNode:
    FieldsValue: dict[str, object] = {
        "owner": OwnerValue,
        "refcount": 0,
        "f28": Parameter,
        "f48": None,
        "f50": -1,
        "f30": 0,
        "f54": 0,
        "f5c": 0,
        "f60": None,
        "f68": 0,
        "has_f78": 0,
        "f80": MakePoint(),
        "fa0": MakePoint(),
        "fc0": MakePoint(),
        "has_fe0": 0,
        "has_ff0": 0,
        "pt_flags": 0,
        "retaining_handles": (),
    }
    return ArchiveNode(RuntimeClass("ParallelPlaneDistanceDim_c", 1), FieldsValue)
