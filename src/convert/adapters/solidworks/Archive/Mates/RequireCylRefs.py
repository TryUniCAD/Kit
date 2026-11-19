from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadRows,
    RequireNode,
)


# the faceted cylinder snapshot and the selected persistent face have separate object graphs
def RequireCylRefs(
    Stored: Mapping[str, object], Selected: Mapping[str, object]
) -> None:
    Component = RequireNode(Stored.get("f58"), "moCompRefCylinder_c").FieldsValue
    Geometry = RequireNode(Component.get("ff8"), "moRefCylinder_c").FieldsValue
    Facet = RequireNode(Component.get("fb0"), "moFacetedData_c").FieldsValue
    FaceValue = RequireNode(Selected.get("f58"), "moCompFace_c").FieldsValue
    FaceRef = RequireNode(FaceValue.get("fe8"), "moFaceRef_c").FieldsValue
    FaceRows = ReadRows(FaceRef.get("f10"))
    if (
        FieldInt(Facet, "has_points") != 0
        or FieldInt(Facet, "f58_empty") != 0
        or FieldInt(FaceValue, "alias") != 0
        or FieldInt(FaceRef, "nf0") != 0
        or len(FaceRows) != 5
        or any(
            Geometry.get(GeomField) != Stored.get(SupportField)
            for GeomField, SupportField in (
                ("f6f8", "fd0"),
                ("f710", "fe8"),
                ("f728", "f100"),
            )
        )
    ):
        raise BodyUnsupported("concentric face or snapshot uses unqualified data")
    Cylinder, FirstCap, FirstNull, SecondCap, SecondNull = FaceRows
    RequireNode(Cylinder.get("f08"), "moFromSktEntSurfIdRep_c")
    RequireNode(FirstCap.get("f08"), "moEndFaceSurfIdRep_c")
    RequireNode(SecondCap.get("f08"), "moEndFaceSurfIdRep_c")
    if FirstNull.get("f08") is not None or SecondNull.get("f08") is not None:
        raise BodyUnsupported("concentric face support requires its two null entries")
