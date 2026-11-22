from convert.adapters.solidworks.Archive.Construction.Assembly.Bounds.MakeChildBox import (
    MakeChildBox,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.CheckAsmChild import (
    CheckAsmChild,
)
from convert.adapters.solidworks.Archive.Construction.AssemblyTargets.TargetDocument import (
    TargetDocument,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# recursive placement must retain the complete generated part graph and neutral plan instead of accepting a decoded or file backed surrogate
def MakePartTarget(ChildValue: PartCandidate) -> TargetDocument:
    if type(ChildValue) is not PartCandidate:
        raise TypeError(
            "a part target requires the actual complete generated candidate"
        )
    CheckAsmChild(ChildValue)
    return TargetDocument(
        ChildValue.SystemValue.RootValue,
        ChildValue.SystemValue.ManagerValue,
        ChildValue.CurrentConfig,
        ChildValue.HeaderValue,
        ChildValue.TopHeader,
        ChildValue.ManagerHeader,
        tuple(
            ArchiveNode.RequireNode(NodeValue)
            for NodeValue in ChildValue.ResolvedValue.RootsValue
        ),
        MakeChildBox(ChildValue),
        (),
        (),
        0,
        ChildValue.ConfigValue,
        ChildValue.ResolvedValue,
        ChildValue.StreamsValue,
        ChildValue.BytesValue,
    )
