from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyInput import (
    AssemblyInput,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyState import (
    AssemblyState,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Metadata.MakeAsmCommon import (
    MakeAsmCommon,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Xml.MakeAsmKeys import (
    MakeAsmKeys,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Xml.MakeAsmTree import (
    MakeAsmTree,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Definition.ModelDefGraph import ModelDefGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Container.Format import (
    KComponentTreeStream,
    KeywordsStream,
)


# flat assembly indexes must retain their existing wire namespace while sharing independently rooted headers definition and history with recursive layouts
def MakeAsmAux(
    StateValue: AssemblyState,
    ChildValue: PartCandidate,
    InputValue: AssemblyInput,
    HeadersValue: tuple[ArchiveNode, ArchiveNode],
    ManagerHeader: ArchiveNode,
    DefinitionValue: ModelDefGraph,
    References: tuple[ArchiveNode, ...],
) -> dict[str, bytes]:
    StreamsValue = MakeAsmCommon(
        InputValue, HeadersValue, ManagerHeader, DefinitionValue
    )
    StreamsValue.update(
        {
            KeywordsStream: MakeAsmKeys(
                StateValue, HeadersValue[0], ChildValue, References
            ),
            KComponentTreeStream: MakeAsmTree(
                StateValue, HeadersValue[0], ChildValue, References
            ),
        }
    )
    return StreamsValue
