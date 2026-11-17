from convert.adapters.solidworks.Archive.Construction.Model.MakeSelfComp import (
    MakeSelfComp,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import RequireNode


# component plane references need constructor state and exclusive component ownership without captured records
def CompRefFields(Component: ArchiveNode) -> dict[str, object]:
    if Component.ClassValue.NameValue == "moUnitComponent_c":
        OwnerValue = Component.FieldsValue.get("owner")
        if (
            not isinstance(OwnerValue, ArchiveNode)
            or Component.FieldsValue.get("has_ext") != 0
        ):
            raise ValueError(
                "plane references require a nonexternal actual model component"
            )
        Component = MakeSelfComp(OwnerValue)
    else:
        Component = RequireNode(Component, "moChainComponent_c")
    Result: dict[str, object] = dict.fromkeys(
        (
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
        ),
        0,
    )
    Result.update(dict.fromkeys(("f90", "f94", "f98", "f9c"), -1))
    Result.update({"f58": Component, "f4c": 19000})
    return Result
