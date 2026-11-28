from convert.adapters.solidworks.Archive.Construction.ConcentricMates.CylFaceBuild import (
    CylFaceBuild,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# detached face snapshots retain the actual kernel face and atom without inventing point selections
def MakeCylFacet(FaceValue: CylFaceBuild) -> ArchiveNode:
    return ArchiveNode(
        RuntimeClass("moFacetedData_c", 1),
        {
            "has_points": 0,
            "f40": FaceValue.FaceNodeId,
            "f50": FaceValue.BodyAtom,
            **dict.fromkeys(("f44", "f48", "f4c", "f54"), -1),
            "f14": 0,
            "f58_empty": 0,
            "f58": f"moFromSktEntSurfIdRep_c,{FaceValue.FeatureId},{FaceValue.ArcMarker}, \n",
        },
    )
