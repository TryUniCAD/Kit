from convert.adapters.solidworks.Archive.Construction.Chamfers.ChmfRefOwners import (
    MakeChmfNode,
)
from convert.adapters.solidworks.Archive.Construction.Model.MakeSelfComp import (
    MakeSelfComp,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.CompRefFields import (
    CompRefFields,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# the removed boundary pairs its end carrier with all four historical sketch sides
def MakeShellCap(
    Model: ArchiveNode, AtomId: int, Carriers: tuple[ArchiveNode, ...]
) -> ArchiveNode:
    References = [{"f08": Value} for Value in (*Carriers, None)]
    FaceValue = MakeChmfNode(
        "moFaceRef_c",
        {
            "f60": 1,
            "f64": 0,
            "f08": len(References),
            "fe8": 768,
            "f70": 0,
            "f28": 1e100,
            "f30": 1e100,
            "f40": None,
            "f10": References,
            "f48": 0,
            "nd0": 0,
            "fd0": [],
            "fec": 19000,
            "has_f18": 0,
            "nf0": 0,
            "ff0": [],
        },
    )
    Fields = CompRefFields(MakeSelfComp(Model))
    Fields.update(f18=AtomId, f1c=AtomId, has_alias=0, fe8=FaceValue, ff0=None)
    return MakeChmfNode("moCompFace_c", Fields)
