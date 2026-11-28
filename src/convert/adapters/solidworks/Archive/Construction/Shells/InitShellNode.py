from convert.adapters.solidworks.Archive.Construction.Chamfers.ChmfRefOwners import (
    MakeChmfNode,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeObList import (
    MakeObList,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.AtomSeeds import (
    KAtomLists,
    KAtomWords,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.InitFeatureMut import (
    InitFeatureMut,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# shell construction starts with the shared empty body feature state and its ordinary inward mode
def InitShellNode(
    Model: ArchiveNode, NameValue: str, Settings: PartBuildInput
) -> ArchiveNode:
    Feature = MakeChmfNode("moShell_c", {})
    InitFeatureMut(Feature, NameValue, Model, Settings.TargetValue)
    Fields = Feature.FieldsValue
    Fields.update(dict.fromkeys(KAtomWords, 0))
    Fields.update({KeyValue: [] for KeyValue in KAtomLists})
    Fields.update(
        f35c=0,
        f368=MakeObList(),
        f388=MakeObList(),
        f4a0=1,
        f6e0=None,
        f758=None,
        f780=MakeObList(),
        f7a0=0,
        f820=0,
        f830=MakeChmfNode("suObList", MakeObList()),
        f838=MakeChmfNode("suObList", MakeObList()),
        f850=None,
    )
    return Feature
