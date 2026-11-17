from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# the unregistered plane handle must retain its inline plane and an exclusively owned self component copy
def MakeSheetRef(
    PlaneValue: ArchiveNode, OwnerValue: ArchiveNode, VersionValue: int
) -> ArchiveNode:
    if PlaneValue.FieldsValue["f08"] != -1:
        raise ValueError(
            "drawing sheet plane handle must precede persistent allocation"
        )
    FieldsValue: dict[str, object] = {
        NameValue: 0
        for NameValue in (
            "f68",
            "f18",
            "f1c",
            "f20",
            "f30",
            "f70",
            "f84",
            "fa0",
            "f34",
            "f48",
            "has_fb0",
            "has_fb8",
            "has_fc0",
            "has_fc8",
            "has_fd0",
        )
    }
    FieldsValue.update({NameValue: -1 for NameValue in ("f90", "f94", "f98", "f9c")})
    FieldsValue.update(
        {
            "f58": ArchiveNode(
                RuntimeClass("moUnitComponent_c", 1),
                {"owner": OwnerValue, "has_ext": 0},
            ),
            "f4c": VersionValue,
            "ff0": {"f00": -1, "f08": 2592000},
            "ff8": PlaneValue,
            "f100": 0,
        }
    )
    return ArchiveNode(RuntimeClass("moCompRefPlane_c", 1), FieldsValue)
