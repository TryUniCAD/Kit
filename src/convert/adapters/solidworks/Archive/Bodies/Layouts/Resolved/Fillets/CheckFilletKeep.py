from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    ReadRows,
    RequireNode,
    RequireRecord,
)


# edge and face keepers have different row cardinality and the edge keeper retains the actual selection
def CheckFilletKeep(FieldsValue: Mapping[str, object]) -> None:
    EdgeValues = RequireRecord(FieldsValue["f820"])
    FaceValues = RequireRecord(FieldsValue["f828"])
    RowsValue = ReadRows(RequireRecord(EdgeValues["f18"])["items"])
    EdgeRefs = ReadRows(RequireRecord(EdgeValues["ff0"])["items"])
    if (
        len(RowsValue) != 2
        or len(EdgeRefs) != 1
        or ReadRows(RequireRecord(FaceValues["f18"])["items"])
        or ReadRows(RequireRecord(FaceValues["fe0"])["items"])
    ):
        raise BodyUnsupported("unsupported SOLIDWORKS fillet keeper inventory")
    BaseRow, FilletRow = RowsValue
    _ = RequireNode(RequireRecord(BaseRow["id"])["f08"], "moSurfaceIdRep_c")
    _ = RequireNode(RequireRecord(FilletRow["id"])["f08"], "moFilletSurfIdRep_c")
    _ = RequireNode(EdgeRefs[0]["o"], "moEdgeRef_c")
