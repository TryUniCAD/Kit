from convert.adapters.solidworks.Archive.Construction.Origin.OriginGraph import (
    OriginGraph,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.CompRefFields import (
    CompRefFields,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakePointRef import (
    MakePointRef,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt


# external selection needs a copied same owner component and the origin log time rather than document filetime
def MakeOriginRef(OriginValue: OriginGraph) -> ArchiveNode:
    ProfileValue, PointValue = OriginValue.ProfileValue, OriginValue.PointValue
    OwnerValue = ArchiveNode.RequireNode(ProfileValue.FieldsValue["owner"])
    FieldsValue = CompRefFields(ArchiveNode.RequireNode(OwnerValue.FieldsValue["f990"]))
    FieldsValue.update(
        {
            "ff0": {"f00": FieldInt(ProfileValue.FieldsValue, "f08"), "f08": 2592000},
            "f0f8": MakePointRef(OriginValue.SketchValue, (PointValue,), PointValue),
            "f100": FieldInt(PointValue.FieldsValue, "f0c"),
        }
    )
    return ArchiveNode(RuntimeClass("moCompSketchEntHandle_c", 1), FieldsValue)
