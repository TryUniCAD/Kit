from convert.adapters.solidworks.Archive.Construction.Files.MakeFileHandle import (
    MakeFileHandle,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.FieldRecord import (
    FieldRecord,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Construction.Files.ReadFileText import (
    ReadFileText,
)


# linked shared definitions project semantic generated identity into new parent owned handles without mutating the independently generated child graph
def MakeSharedCopy(FileValue: ArchiveNode) -> dict[str, object]:
    SharedValue = dict(FieldRecord(FileValue.FieldsValue["shared"]))
    for FieldName in ("h10", "h18"):
        SharedValue[FieldName] = MakeFileHandle(ReadFileText(SharedValue[FieldName]))
    return SharedValue
