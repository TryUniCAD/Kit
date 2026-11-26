from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# native names belong to their retained name node rather than nearby byte strings
def ReadNativeName(NodeValue: ArchiveNode) -> str:
    NameValue = RequireNative(NodeValue.FieldsValue.get("f18"), "moNodeName_c")
    TextValue = NameValue.FieldsValue.get("f08")
    if isinstance(TextValue, tuple):
        TupleValue = CastValue(tuple[object, ...], TextValue)
        TextValue = (
            TupleValue[1] if len(TupleValue) == 2 and TupleValue[0] == "A" else None
        )
    if type(TextValue) is not str or not TextValue:
        raise ValueError("typed model node has no serialized name")
    return TextValue
