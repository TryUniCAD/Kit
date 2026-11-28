from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyState import (
    AssemblyState,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Metadata.Information.AsmInfoInput import (
    AsmInfoInput,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Metadata.Information.InfoConfigName import (
    InfoConfigName,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Metadata.Information.MakeInfoXml import (
    MakeInfoXml,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Metadata.Information.ReadInfoFile import (
    ReadInfoFile,
)
from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import (
    SelfFileInput,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# the shared constructor must have every information owner in memory before any parent container exists
def MakeAsmInfo(
    StateValue: AssemblyState,
    HeadersValue: tuple[ArchiveNode, ArchiveNode],
    OutputValue: SelfFileInput,
    InputValue: AsmInfoInput,
) -> bytes:
    NameValue = InfoConfigName(StateValue)
    FilePath, SavedAt = ReadInfoFile(StateValue, HeadersValue, OutputValue)
    return MakeInfoXml(
        StateValue.RootValue,
        OutputValue.PathName,
        FilePath,
        NameValue,
        SavedAt,
        InputValue,
    )
