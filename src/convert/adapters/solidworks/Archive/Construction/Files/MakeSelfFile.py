from convert.adapters.solidworks.Archive.Construction.Files.MakeFileConfig import (
    MakeFileConfig,
)
from convert.adapters.solidworks.Archive.Construction.Files.MakeFileDef import (
    MakeFileDef,
)
from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import (
    SelfFileInput,
)
from convert.adapters.solidworks.Archive.Construction.Model.RequireRootNode import (
    RequireRootNode,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Construction.Model.GraphValue import (
    FieldInt,
    FieldText,
)


# a generated self record must retain actual model and configuration identity without borrowing a saved directory entry or inspecting target paths
def MakeSelfFile(
    ModelValue: ArchiveNode,
    HeaderValue: ArchiveNode,
    ConfigValue: ArchiveNode,
    InputValue: SelfFileInput,
) -> ArchiveNode:
    RequireRootNode(ModelValue, "moPart_c")
    RequireRootNode(HeaderValue, "moHeader_c")
    if type(InputValue) is not SelfFileInput or not HeaderValue.FieldsValue["fec"]:
        raise ValueError(
            "native self identity requires explicit target input and the owning model header"
        )
    if InputValue.SavedAt < FieldInt(HeaderValue.FieldsValue, "f50"):
        raise ValueError("native save event precedes the modeled modification time")
    NameNode = ArchiveNode.RequireNode(ModelValue.FieldsValue["f18"])
    RequireRootNode(NameNode, "moNodeName_c")
    SharedFields = MakeFileDef(
        InputValue,
        FieldText(NameNode.FieldsValue, "f08"),
        FieldInt(HeaderValue.FieldsValue, "f70"),
    )
    return ArchiveNode(
        RuntimeClass("moExtObject_c", 1),
        {
            "shared": SharedFields,
            "f58": 0,
            "f60": InputValue.SavedAt,
            "f48": 1,
            "f4c": 0,
            "f78": -1,
            "refcfg": MakeFileConfig(ModelValue, ConfigValue),
            "f54": 0,
            "f70": 0,
            "f50": 0,
        },
    )
