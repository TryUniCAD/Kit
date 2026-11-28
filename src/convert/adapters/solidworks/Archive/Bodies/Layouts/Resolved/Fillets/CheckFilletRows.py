from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    ReadRows,
    RequireNode,
    RequireRecord,
)


# the witnessed reader scope has one selected edge and one radial row with separate saved result owners
def CheckFilletRows(FieldsValue: Mapping[str, object]) -> None:
    AlternateLists = (
        FieldsValue[FieldName] for FieldName in ("f850", "f858", "f860", "f870")
    )
    if (
        any(
            not isinstance(RowsValue, ArchiveNode)
            or RowsValue.ClassValue.NameValue != "suObList"
            or ReadRows(RowsValue.FieldsValue["items"])
            for RowsValue in AlternateLists
        )
        or any(
            FieldsValue[FieldName] is not None
            for FieldName in (
                "f830",
                "f838",
                "f840",
                "f878",
                "f880",
                "f888",
                "f8b8",
                "fc40",
            )
        )
        or any(
            ReadRows(RequireRecord(FieldsValue[FieldName])["items"])
            for FieldName in ("f8f8", "f9e8")
        )
    ):
        raise BodyUnsupported("unsupported SOLIDWORKS fillet auxiliary owner")
    for FieldName, Owner in (("f848", "moCompEdge_c"), ("f868", "edgeRadiusObject_c")):
        ItemsValue = ReadRows(
            RequireNode(FieldsValue[FieldName], "suObList").FieldsValue["items"]
        )
        if len(ItemsValue) != 1:
            raise BodyUnsupported(
                "SOLIDWORKS ordinary fillet needs one edge and radius"
            )
        _ = RequireNode(ItemsValue[0]["o"], Owner)
    FaceRows = ReadRows(FieldsValue["f9b8"])
    RadiusRows = ReadRows(FieldsValue["fbf0"])
    if len(FaceRows) != 1 or len(RadiusRows) != 1:
        raise BodyUnsupported("unsupported SOLIDWORKS fillet result inventory")
    _ = RequireNode(FaceRows[0]["k"], "moCompFace_c")
    _ = RequireNode(FaceRows[0]["v"], "moCompEdge_c")
    _ = RequireNode(RadiusRows[0]["edge"], "moCompEdge_c")
