from convert.adapters.solidworks.Archive.Construction.Assembly.Occurrences.MakeSharedCopy import (
    MakeSharedCopy,
)
from convert.adapters.solidworks.Archive.Construction.Files.MakeFileConfig import (
    MakeFileConfig,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import RequireNode


# every side and cap reference must share the actual generated child file and configuration once
def MakeCylFile(ChildValue: PartCandidate) -> ArchiveNode:
    ChildFile = RequireNode(
        ChildValue.HeaderValue.FieldsValue.get("f38"), "moExtObject_c"
    )
    FieldsValue: dict[str, object] = dict.fromkeys(
        ("f48", "f4c", "f50", "f54", "f58", "f60", "f70", "f78"), 0
    )
    FieldsValue.update(
        refcfg=MakeFileConfig(
            ChildValue.SystemValue.RootValue, ChildValue.CurrentConfig
        ),
        shared=MakeSharedCopy(ChildFile),
    )
    return ArchiveNode(RuntimeClass("moExtObject_c", 1), FieldsValue)
