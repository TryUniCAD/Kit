from convert.adapters.solidworks.Archive.Construction.Model.RequireRootNode import (
    RequireRootNode,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue
from convert.adapters.solidworks.Archive.Construction.Model.GraphValue import (
    FieldInt,
    FieldText,
)


# ordinary model self identity must name its actual selected configuration
def MakeFileConfig(
    ModelValue: ArchiveNode, ConfigValue: ArchiveNode
) -> dict[str, object]:
    ExpectedClass = (
        "moConfiguration_c"
        if ModelValue.ClassValue == RuntimeClass("moAssembly_c", 1)
        else "moPartConfiguration_c"
    )
    RequireRootNode(ConfigValue, ExpectedClass)
    if ConfigValue.FieldsValue.get("owner") is not ModelValue:
        raise ValueError(
            "self identity configuration belongs to a different actual model"
        )
    NameNode = ArchiveNode.RequireNode(ConfigValue.FieldsValue["f18"])
    RequireRootNode(NameNode, "moNodeName_c")
    LocalId = FieldInt(ConfigValue.FieldsValue, "f08")
    if not 0 <= LocalId < 0x7FFFFFFF:
        raise ValueError(
            "self identity configuration requires its allocated local identifier"
        )
    return {
        "f08": CStringValue(FieldText(NameNode.FieldsValue, "f08"), True),
        "f10": LocalId,
    }
