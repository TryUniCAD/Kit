from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# the native saved contour must retain only the actual closed circle in its sole loop
def CheckCircChain(Profile: ArchiveNode, ArcMark: int) -> None:
    CacheValue = NativeRecord(Profile.FieldsValue.get("d5c0"))
    RowsValue = NativeRows(CacheValue.get("f2a8"))
    if CacheValue.get("f2b0") != 1 or len(RowsValue) != 1:
        raise ValueError("saved circle lacks its single closed contour")
    ChainValue = RequireNative(RowsValue[0].get("chain"), "moSketchChain_c")
    Fields = ChainValue.FieldsValue
    Member = NativeRecord(Fields.get("f08"))
    Loops = NativeRecord(Fields.get("f60"))
    if (
        NativeRows(Member.get("items")) != ({"v": ArcMark},)
        or NativeRows(Loops.get("items")) != ({"v": 0},)
        or Fields.get("nmap") != 0
        or Fields.get("end_map")
        or Fields.get("fc0") is not None
        or Fields.get("fc8") is not None
    ):
        raise ValueError("saved circle contour disagrees with its live arc and profile")
