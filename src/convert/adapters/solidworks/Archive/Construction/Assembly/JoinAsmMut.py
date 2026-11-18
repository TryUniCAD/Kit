from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Archive.Construction.Assembly.AsmGraphState import (
    AsmGraphState,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyState import (
    AssemblyState,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyStreams import (
    AssemblyStreams,
)


# assembly layouts must preserve native serialization order and original graph identities while adding their independently generated metadata streams
def JoinAsmMut(
    StateValue: AssemblyState,
    GraphValue: AsmGraphState,
    StreamsValue: dict[str, bytes],
) -> AssemblyStreams:
    StreamsValue.update(
        {
            "Contents/Config-0": GraphValue.ConfigBytes,
            "Contents/Config-0-ResolvedFeatures": GraphValue.ResolvedBytes,
            "Contents/Config-0-MatesList": GraphValue.MatesBytes,
            "Contents/CMgr": WriteCmgrMut(StateValue.ManagerValue, 19000),
        }
    )
    return AssemblyStreams(
        StreamsValue,
        GraphValue.ConfigValue,
        GraphValue.ResolvedValue,
        GraphValue.MatesValue,
        GraphValue.ManagerHeader,
        GraphValue.DefinitionValue,
    )
