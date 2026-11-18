from typing import cast as CastValue
from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyInput import (
    AssemblyInput,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyState import (
    AssemblyState,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyStreams import (
    AssemblyStreams,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Headers.MakeAsmMgrHdr import (
    MakeAsmMgrHdr,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Metadata.MakeAsmAux import (
    MakeAsmAux,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Definition.Construction.MakeAssemblyDef import (
    MakeAssemblyDef,
)
from convert.adapters.solidworks.Archive.Mates.WriteMatesMut import WriteMatesMut
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut


# assembly streams serialize their actual configuration resolved and mate maps in native dependency order with separate manager and metadata contexts
def EmitAsmStreams(
    StateValue: AssemblyState,
    ChildValue: PartCandidate,
    InputValue: AssemblyInput,
    HeadersValue: tuple[ArchiveNode, ArchiveNode],
    References: tuple[ArchiveNode, ...],
    MateValue: ArchiveNode | tuple[ArchiveNode, ...],
) -> AssemblyStreams:
    HeaderValue = HeadersValue[0]
    ConfigBytes, ConfigValue = WriteConfigMut(StateValue.RootValue, 19000, HeaderValue)
    ContextValue = {
        "model_compressed_stream": 1,
        "model_is_part": 0,
        "cmgr_f658": CastValue(int, StateValue.ManagerValue.FieldsValue["f658"]),
    }
    ResolvedBytes, ResolvedValue = WriteResolMut(
        StateValue.FeatureValues, None, 19000, ConfigValue.MapValue, ContextValue
    )
    MateRoots = (MateValue,) if isinstance(MateValue, ArchiveNode) else MateValue
    MatesBytes, MatesValue = WriteMatesMut(MateRoots, ResolvedValue)
    ManagerHeader = MakeAsmMgrHdr(StateValue, InputValue.OutputValue.SavedAt)
    DefinitionValue = MakeAssemblyDef(
        InputValue.DefinitionValue, InputValue.SavePartValues
    )
    StreamsValue = MakeAsmAux(
        StateValue,
        ChildValue,
        InputValue,
        HeadersValue,
        ManagerHeader,
        DefinitionValue,
        References,
    )
    StreamsValue.update(
        {
            "Contents/Config-0": ConfigBytes,
            "Contents/Config-0-ResolvedFeatures": ResolvedBytes,
            "Contents/Config-0-MatesList": MatesBytes,
            "Contents/CMgr": WriteCmgrMut(StateValue.ManagerValue, 19000),
        }
    )
    return AssemblyStreams(
        StreamsValue,
        ConfigValue,
        ResolvedValue,
        MatesValue,
        ManagerHeader,
        DefinitionValue,
    )
