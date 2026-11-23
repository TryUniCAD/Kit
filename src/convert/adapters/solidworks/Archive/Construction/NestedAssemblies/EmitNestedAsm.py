from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyInput import (
    AssemblyInput,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyState import (
    AssemblyState,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyStreams import (
    AssemblyStreams,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.AsmGraphState import (
    AsmGraphState,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.JoinAsmMut import (
    JoinAsmMut,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Metadata.MakeAsmCommon import (
    MakeAsmCommon,
)
from convert.adapters.solidworks.Archive.Construction.AssemblyTargets.TargetDocument import (
    TargetDocument,
)
from convert.adapters.solidworks.Archive.Construction.NestedAssemblies.MakeNestedKeys import (
    MakeNestedKeys,
)
from convert.adapters.solidworks.Archive.Construction.NestedAssemblies.MakeNestedTree import (
    MakeNestedTree,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Container.Format import (
    KComponentTreeStream,
    KeywordsStream,
)


# recursive assembly serialization must share proven binary header and history emission while deriving its own complete document index closure
def EmitNestedAsm(
    StateValue: AssemblyState,
    InputValue: AssemblyInput,
    HeadersValue: tuple[ArchiveNode, ArchiveNode],
    GraphValue: AsmGraphState,
    TargetValue: TargetDocument,
) -> AssemblyStreams:
    StreamsValue = MakeAsmCommon(
        StateValue,
        InputValue,
        HeadersValue,
        GraphValue.ManagerHeader,
        GraphValue.DefinitionValue,
    )
    StreamsValue.update(
        {
            KeywordsStream: MakeNestedKeys(TargetValue),
            KComponentTreeStream: MakeNestedTree(TargetValue),
        }
    )
    return JoinAsmMut(StateValue, GraphValue, StreamsValue)
