from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import RequireNode


# wrapper construction keeps access stamps transforms ownership and solver state independent until their actual operations apply
def WrapperFields(
    Reference: ArchiveNode, *, AxisSupport: bool = False
) -> dict[str, object]:
    _ = RequireNode(Reference, "moCompRefAxis_c" if AxisSupport else "moCompRefPlane_c")
    Result: dict[str, object] = dict.fromkeys(
        ("f68", "f6c", "has_f10", "has_f18", "f20", "f50", "f34", "f30", "f98"), 0
    )
    Result.update(
        {
            "f58": Reference,
            "f60": None,
            "f08": 101,
            "f0c": -1,
            "f74": -12345,
            "f78": -12345,
            "f7c": -12345,
            "f70": 19000,
            "f38": -1,
        }
    )
    return Result
