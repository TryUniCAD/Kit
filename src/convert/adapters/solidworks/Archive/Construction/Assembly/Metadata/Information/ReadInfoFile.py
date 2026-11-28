from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyState import (
    AssemblyState,
)
from convert.adapters.solidworks.Archive.Construction.Files.MakeFileConfig import (
    MakeFileConfig,
)
from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import (
    SelfFileInput,
)
from convert.adapters.solidworks.Archive.Construction.Model.RequireRootNode import (
    RequireRootNode,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadFileKey
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadNodeName,
    RequireNode,
)


# system publication needs the same linked file event and locator that the two document headers carry
def ReadInfoFile(
    StateValue: AssemblyState,
    HeadersValue: tuple[ArchiveNode, ArchiveNode],
    OutputValue: SelfFileInput,
) -> tuple[str, int]:
    ModelHeader, TopHeader = HeadersValue
    RequireRootNode(StateValue.RootValue, "moAssembly_c")
    RequireRootNode(ModelHeader, "moHeader_c")
    RequireRootNode(TopHeader, "moHeader_c")
    FileValue = RequireNode(ModelHeader.FieldsValue.get("f38"), "moExtObject_c")
    RequireRootNode(FileValue, "moExtObject_c")
    FileKey = ReadFileKey(FileValue)
    SavedAt = FieldInt(FileValue.FieldsValue, "f60")
    if (
        ModelHeader is TopHeader
        or TopHeader.FieldsValue.get("f38") is not FileValue
        or FileKey
        != (
            ReadNodeName(StateValue.RootValue),
            OutputValue.PathName,
            3,
            FieldInt(ModelHeader.FieldsValue, "f70"),
        )
        or FileKey[3] != FieldInt(TopHeader.FieldsValue, "f70")
        or SavedAt != OutputValue.SavedAt
        or FileValue.FieldsValue.get("refcfg")
        != MakeFileConfig(StateValue.RootValue, StateValue.CurrentConfig)
    ):
        raise ValueError(
            "assembly information requires the actual paired self file and save event"
        )
    return FileKey[1], SavedAt
