from convert.adapters.solidworks.Archive.Construction.Model.RequireRootNode import (
    RequireRootNode,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.CompRefFields import (
    CompRefFields,
)
from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import (
    PrincipalFrame,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# the origin owns an exclusive plane wrapper and copied self component while its principal datum stays an actual shared feature
def MakeOriginRef(
    PlaneValue: ArchiveNode, OwnerValue: ArchiveNode, AxisValue: str
) -> ArchiveNode:
    RequireRootNode(PlaneValue, "moRefPlane_c")
    RequireRootNode(OwnerValue, "moPart_c")
    FrameValue = PrincipalFrame(AxisValue)
    PlaneId = PlaneValue.FieldsValue.get("f08")
    if (
        type(PlaneId) is not int
        or not 0 <= PlaneId < 0x7FFFFFFF
        or PlaneValue.FieldsValue.get("owner") is not OwnerValue
    ):
        raise ValueError(
            "origin support must be a registered principal plane in its actual owning part"
        )
    DataValue = ArchiveNode.RequireNode(PlaneValue.FieldsValue["f6f8"])
    RequireRootNode(DataValue, "moDefaultRefPlnData_c")
    if (
        DataValue.FieldsValue["normal"]
        != dict(zip(("x", "y", "z"), FrameValue.NormalValue, strict=True))
        or PlaneValue.FieldsValue["f34c"] != 0
    ):
        raise ValueError(
            "origin plane kind differs from its actual principal plane geometry"
        )
    Component = ArchiveNode.RequireNode(OwnerValue.FieldsValue["f990"])
    RequireRootNode(Component, "moUnitComponent_c")
    FieldsValue = CompRefFields(Component)
    FieldsValue.update(
        {
            "ff0": {"f00": PlaneId, "f08": 2592000},
            "ff8": None,
            "f100": {"x": 1, "y": 2, "z": 3}[AxisValue],
        }
    )
    return ArchiveNode(RuntimeClass("moCompRefPlane_c", 1), FieldsValue)
