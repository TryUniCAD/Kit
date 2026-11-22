from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# ordinary new display dimensions start without an assigned style favorite while retaining their own typed favorite handle
def MakeFavorite() -> ArchiveNode:
    return ArchiveNode(
        RuntimeClass("moFavoriteHandle_c", 1), {"f08": 0, "f0c": -1, "f10": 0}
    )
