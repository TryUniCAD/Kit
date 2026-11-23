from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyState import (
    AssemblyState,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Xml.MakeAsmKeyIndex import (
    MakeAsmKeyIndex,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# assembly keyword rows derive native roles from actual generated roots and sort their independent lexical identifier namespace before framing computed xml
def MakeAsmKeys(
    StateValue: AssemblyState,
    HeaderValue: ArchiveNode,
    ChildValue: PartCandidate,
    References: tuple[ArchiveNode, ...],
) -> bytes:
    ChildFile = ArchiveNode.RequireNode(ChildValue.HeaderValue.FieldsValue["f38"])
    return MakeAsmKeyIndex(
        StateValue.RootValue,
        StateValue.FeatureValues,
        HeaderValue,
        StateValue.CurrentConfig,
        tuple((Reference, ChildFile) for Reference in References),
    )
