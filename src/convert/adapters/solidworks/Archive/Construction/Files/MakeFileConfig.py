from convert.adapters.solidworks.Archive.Construction.Model.RequireRootNode import (
    RequireRootNode,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    FieldText,
)


# ordinary file references must name the actual selected configuration while drawing identity retains its distinct absent configuration branch
def MakeFileConfig(
    ModelValue: ArchiveNode, ConfigValue: ArchiveNode | None
) -> dict[str, object]:
    ClassName = ModelValue.ClassValue.NameValue
    if ClassName == "moDrawing_c":
        if ConfigValue is not None:
            raise ValueError(
                "drawing self identity cannot publish an ordinary selected configuration"
            )
        return {"f08": CStringValue("", True), "f10": -1}
    ExpectedClass = {
        "moPart_c": "moPartConfiguration_c",
        "moAssembly_c": "moConfiguration_c",
    }[ClassName]
    if ConfigValue is None:
        raise ValueError(
            "ordinary model self identity requires its actual active configuration"
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
