from typing import cast as CastValue
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Construction.Assembly.AsmGraphState import (
    AsmGraphState,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyInput import (
    AssemblyInput,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyState import (
    AssemblyState,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Headers.MakeAsmMgrHdr import (
    MakeAsmMgrHdr,
)
from convert.adapters.solidworks.Archive.Definition.Construction.MakeAssemblyDef import (
    MakeAssemblyDef,
)
from convert.adapters.solidworks.Archive.Mates.WriteMatesMut import WriteMatesMut
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut


# each assembly layout must share the same configuration resolved and mate map traversal before any separately rooted metadata is emitted
def MakeAsmGraphs(
    StateValue: AssemblyState,
    InputValue: AssemblyInput,
    HeaderValue: ArchiveNode,
    MateValues: tuple[ArchiveNode, ...],
) -> AsmGraphState:
    ConfigBytes, ConfigValue = WriteConfigMut(StateValue.RootValue, 19000, HeaderValue)
    ContextValue = {
        "model_compressed_stream": 1,
        "model_is_part": 0,
        "cmgr_f658": CastValue(int, StateValue.ManagerValue.FieldsValue["f658"]),
    }
    ResolvedBytes, ResolvedValue = WriteResolMut(
        StateValue.FeatureValues, None, 19000, ConfigValue.MapValue, ContextValue
    )
    MatesBytes, MatesValue = WriteMatesMut(MateValues, ResolvedValue)
    return AsmGraphState(
        ConfigBytes,
        ConfigValue,
        ResolvedBytes,
        ResolvedValue,
        MatesBytes,
        MatesValue,
        MakeAsmMgrHdr(StateValue, InputValue.OutputValue.SavedAt),
        MakeAssemblyDef(InputValue.DefinitionValue, InputValue.SavePartValues),
    )
