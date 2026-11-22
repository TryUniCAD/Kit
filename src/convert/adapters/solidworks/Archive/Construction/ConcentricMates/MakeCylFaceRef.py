from convert.adapters.solidworks.Archive.Construction.ConcentricMates.CylFaceBuild import (
    CylFaceBuild,
)
from convert.adapters.solidworks.Archive.Construction.ConcentricMates.MakeCylSurface import (
    MakeCylSurface,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# the selected physical lateral face owns its circle role and both ordered cap and null slots
def MakeCylFaceRef(FaceValue: CylFaceBuild, FileValue: ArchiveNode) -> ArchiveNode:
    SideValue = MakeCylSurface(
        "moFromSktEntSurfIdRep_c", FaceValue, FileValue, {"f38": FaceValue.ArcMarker}
    )
    RowsValue: list[dict[str, ArchiveNode | None]] = [{"f08": SideValue}]
    for Selector, Contour in FaceValue.CapSelectors:
        RowsValue.extend(
            (
                {
                    "f08": MakeCylSurface(
                        "moEndFaceSurfIdRep_c",
                        FaceValue,
                        FileValue,
                        {"f38": Selector, "f3c": Contour},
                    )
                },
                {"f08": None},
            )
        )
    return ArchiveNode(
        RuntimeClass("moFaceRef_c", 1),
        {
            "f60": 1,
            "f64": 0,
            "f08": len(RowsValue),
            "fe8": 0x200,
            "f70": FaceValue.FaceTag,
            "f28": 1e100,
            "f30": 1e100,
            "f40": None,
            "f10": RowsValue,
            "f48": 0,
            "fd0": [],
            "nd0": 0,
            "fec": 19000,
            "has_f18": 0,
            "ff0": [],
            "nf0": 0,
        },
    )
