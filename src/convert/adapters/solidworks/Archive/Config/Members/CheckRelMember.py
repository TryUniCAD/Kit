from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# prior mapped relation objects can bypass the body guard and still need owner validation
def CheckRelMember(RootValue: ArchiveNode) -> None:
    Fields = RootValue.FieldsValue
    Relations = CastValue(dict[str, object], Fields["f58"])
    Secondary = CastValue(dict[str, object], Fields["fa0"])
    MemberRows = CastValue(list[dict[str, object]], Fields["f1c0"])
    if (
        Relations["items"]
        or Secondary["items"]
        or any(RowValue["o"] is not None for RowValue in MemberRows)
    ):
        raise BodyUnsupported(
            "SOLIDWORKS configuration relation member has unqualified objects"
        )
