from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# lazy native bom creation constructs one empty owned list without adding any table children
def MakeBomMgr(PresentValue: bool) -> ArchiveNode | None:
    if type(PresentValue) is not bool:
        raise TypeError("BOM manager construction requires a boolean presence")
    if not PresentValue:
        return None
    RowValues: list[object] = []
    return ArchiveNode(
        RuntimeClass("moBomInfoMgr_c", 1),
        {"f08": RowValues, "n": len(RowValues)},
    )
