from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Container.Format import KAsmFormatId, KAsmSuffix
from convert.adapters.solidworks.Core.AssemblyPreparation.AsmWriteCaps import (
    KAsmWriteCaps,
)
from convert.adapters.solidworks.Core.Writing.PartWriteInfo import KPartWriteInfo
from interchange.Enums.EnumDocument import Capability

# the canonical writer adds the measured rigid assembly aliases to the existing part route
KSldWriteInfo = ReplaceValue(
    KPartWriteInfo,
    extensions=(*KPartWriteInfo.extensions, KAsmSuffix),
    aliases=(KAsmFormatId,),
    capabilities=KPartWriteInfo.capabilities
    | KAsmWriteCaps
    | {Capability.KExternalRefs, Capability.KNativePayloads},
    native_capabilities=KPartWriteInfo.native_capabilities | KAsmWriteCaps,
    assembly_extensions=(KAsmSuffix,),
    media_types=(
        *KPartWriteInfo.media_types,
        "application/x-solidworks-assembly",
    ),
)
