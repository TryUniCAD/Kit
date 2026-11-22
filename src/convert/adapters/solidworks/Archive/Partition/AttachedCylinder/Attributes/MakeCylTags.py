from convert.adapters.solidworks.Archive.Construction.PlanarMates.SignedStamp import (
    SignedStamp,
)
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode

# an empty kernel session allocates its first body tag before any owned boundary cell
KFirstBodyTag = 1


# the transient allocation follows the actual newly created body cells
def MakeCylTags(NodesValue: tuple[XmtNode, ...]) -> dict[int, int]:
    Result = {
        NodeValue.IndexValue: TagValue
        for TagValue, NodeValue in enumerate(NodesValue, KFirstBodyTag)
    }
    if len(Result) != len(NodesValue) or max(Result.values()) > 0xFFFF:
        raise ValueError("concentric native body or face tag overflow")
    return Result


# the native tracking word packs a transient entity tag and actual tessellation update stamp
def CylTrackWord(TagValue: int, UpdateValue: int) -> int:
    return SignedStamp((TagValue & 0xFFFF) << 16 | (UpdateValue & 0xFFFF))
