from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Container.Format import KInfoValue, KPartSuffix
from convert.adapters.solidworks.Core.Preparation.PartCaps import KPartWriteCaps
from interchange.Enums.EnumDocument import Capability

# the writer owns solely the qualified part destination while the reader still recognizes the other solidworks document kinds
KPartWriteInfo = ReplaceValue(
    KInfoValue,
    extensions=(KPartSuffix,),
    aliases=(),
    capabilities=KPartWriteCaps
    | {
        Capability.KBrep,
        Capability.KProvenance,
        Capability.KRoundtripMeta,
        Capability.KSelections,
    },
    media_types=("application/x-solidworks-part",),
    native_capabilities=KPartWriteCaps
    | {
        Capability.KBrep,
        Capability.KProvenance,
        Capability.KRoundtripMeta,
        Capability.KSelections,
    },
    assembly_extensions=(),
)
