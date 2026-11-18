from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Drawing.Construction.Profiles.OriginVisibility import (
    OriginVisibility,
)
from convert.adapters.solidworks.Drawing.Definition.Profiles.NeedProfileNode import (
    NeedProfileNode,
)


# the ordinary population path needs a complete fresh display object with real folder view and component ownership
def MakeOriginDisplay(
    FolderValue: ArchiveNode, ViewValue: ArchiveNode, Reference: ArchiveNode
) -> ArchiveNode:
    _ = NeedProfileNode(FolderValue, "moDetailFolder_c")
    _ = NeedProfileNode(ViewValue, "moAbsoluteView")
    _ = NeedProfileNode(Reference, "moCompProfile_c")
    if (
        FolderValue.FieldsValue.get("owner") is not ViewValue
        or ViewValue.FieldsValue.get("f630") is not FolderValue
    ):
        raise ValueError("origin display requires the actual view detail folder")
    return ArchiveNode(
        RuntimeClass("moDisplayProfileFeature_c", 1),
        {
            "f50": 0,
            "f30": FolderValue,
            "f40": ViewValue,
            "f48": Reference,
            "f54": 0,
            "f11c": 0,
            "f08": OriginVisibility(),
            "f68": {"n": 0, "items": ()},
            "fb0": {"n": 0, "items": ()},
            "f58": 0,
            "ff8": None,
            "linked": 0,
            "f118": 19000,
            "n1e0": 0,
            "f1e0": (),
            "f200": 1,
        },
    )
