from convert.adapters.solidworks.Archive.Construction.Origin.OriginGraph import (
    OriginGraph,
)
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt


# origin labels must follow the selected actual point ordinal and profile name instead of a saved label
def MakeExternalEnt(WrapperValue: ArchiveNode, OriginValue: OriginGraph) -> ArchiveNode:
    NameNode = ArchiveNode.RequireNode(OriginValue.ProfileValue.FieldsValue["f18"])
    NameValue = ReadStyleText(NameNode.FieldsValue["f08"], "origin name")
    OrdinalValue = FieldInt(OriginValue.PointValue.FieldsValue, "f0c")
    return ArchiveNode(
        RuntimeClass("sgExtEnt_c", 1),
        {
            "f08": WrapperValue,
            "f10": None,
            "f18": None,
            "f20": None,
            "f28": f"Point{OrdinalValue}@{NameValue}",
        },
    )
