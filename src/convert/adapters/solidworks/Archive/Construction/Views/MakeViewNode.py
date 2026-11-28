from convert.adapters.solidworks.Archive.Construction.Geometry.IdentityXform import (
    IdentityXform,
)
from convert.adapters.solidworks.Archive.Construction.Views.ViewMatrix import ViewMatrix
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# indexed views own separate transforms and constructor state without consuming model persistent identifiers
def MakeViewNode(
    NameValue: str,
    IndexValue: int,
    Quaternion: tuple[float, float, float, float] | None,
) -> ArchiveNode:
    Transform = IdentityXform()
    if IndexValue >= 2 and Quaternion is not None:
        Transform.update({"has_matrix": 1, "f08": ViewMatrix(Quaternion)})
    return ArchiveNode(
        RuntimeClass("moView_c", 1),
        {
            "f358": NameValue,
            "f368": Transform,
            "f370": IdentityXform(),
            "f388": 0,
            "f38c": -1,
            "f378": -1.0,
            "n380": 0,
            "f380": (),
            "f360": IndexValue,
            "f394": 0,
            "n398": 0,
            "f3a8": 0,
            "f3b8": 0.0,
            "n3b0": 0,
            "f3c0": 0,
            "f3c8": 0,
        },
    )
