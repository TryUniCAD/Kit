from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    FieldText,
    RequireNode,
)
from convert.adapters.solidworks.Core.TypedMates.Cylinders.CylChild import CylChild


# independent graphics snapshots cannot substitute a transmit index or another body for the selected face
def CheckCylFacet(SupportValue: ArchiveNode, ChildValue: CylChild) -> None:
    Component = RequireNode(SupportValue.FieldsValue.get("f58"), "moCompRefCylinder_c")
    FacetValue = RequireNode(Component.FieldsValue.get("fb0"), "moFacetedData_c")
    FieldsValue = FacetValue.FieldsValue
    FeatureId = FieldInt(ChildValue.FeatureValue.FieldsValue, "f08")
    ExpectedText = f"moFromSktEntSurfIdRep_c,{FeatureId},{ChildValue.ArcMarker}, \n"
    if (
        FieldInt(FieldsValue, "f40") != ChildValue.FaceValue.Integer("node_id")
        or FieldInt(FieldsValue, "f50") != ChildValue.AtomValue
        or FieldText(FieldsValue, "f58") != ExpectedText
        or any(
            FieldInt(FieldsValue, NameValue) != -1
            for NameValue in ("f44", "f48", "f4c", "f54")
        )
    ):
        raise ValueError(
            "concentric faceted snapshot differs from actual face and body identities"
        )
