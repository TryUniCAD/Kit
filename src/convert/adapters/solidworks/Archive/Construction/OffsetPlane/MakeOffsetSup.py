from convert.adapters.solidworks.Archive.Construction.Model.RequireRootNode import (
    RequireRootNode,
)
from convert.adapters.solidworks.Archive.Construction.OffsetPlane.OffsetGraph import (
    OffsetGraph,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.CompRefFields import (
    CompRefFields,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# translated profiles require the actually registered plane and independently owned component wrapper
def MakeOffsetSup(OwnerValue: ArchiveNode, OffsetValue: OffsetGraph) -> ArchiveNode:
    NodeValue = OffsetValue.FeatureValue
    RequireRootNode(NodeValue, "moRefPlane_c")
    DataValue = ArchiveNode.RequireNode(NodeValue.FieldsValue.get("f6f8"))
    PlaneId = NodeValue.FieldsValue.get("f08")
    if (
        NodeValue.FieldsValue.get("owner") is not OwnerValue
        or OffsetValue.DatumValue.FieldsValue.get("owner") is not OwnerValue
        or DataValue.ClassValue != RuntimeClass("moFaceRefPlnData_c", 1)
        or DataValue.FieldsValue.get("f98")
        is not OffsetValue.DistanceValue.DisplayValue
        or type(PlaneId) is not int
        or PlaneId < 0
    ):
        raise ValueError("offset sketch requires its actual local datum and driver")
    Component = ArchiveNode.RequireNode(OwnerValue.FieldsValue.get("f990"))
    RequireRootNode(Component, "moUnitComponent_c")
    FieldsValue = CompRefFields(Component)
    FieldsValue.update(ff0={"f00": PlaneId, "f08": 2592000}, ff8=None, f100=0)
    return ArchiveNode(RuntimeClass("moCompRefPlane_c", 1), FieldsValue)
