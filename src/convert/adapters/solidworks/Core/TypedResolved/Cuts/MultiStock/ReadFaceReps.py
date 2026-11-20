from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# the face incidence must account for the five physical representations and its null terminator
def ReadFaceReps(FaceValue: ArchiveNode) -> tuple[ArchiveNode, ...]:
    Fields = RequireNative(FaceValue, "moFaceRef_c").FieldsValue
    RowsValue = NativeRows(Fields.get("f10"))
    if (
        Fields.get("f08") != 6
        or len(RowsValue) != 6
        or RowsValue[-1].get("f08") is not None
    ):
        raise ValueError("two stock face carrier has alternate incidence")
    return tuple(RequireNative(RowValue.get("f08")) for RowValue in RowsValue[:-1])
