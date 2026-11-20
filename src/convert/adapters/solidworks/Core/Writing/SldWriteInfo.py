from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Container.Format import (
    KAsmFormatId,
    KAsmSuffix,
    KDrawingFormatId,
    KDrawingSuffix,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.AsmWriteCaps import (
    KAsmWriteCaps,
)
from convert.adapters.solidworks.Core.Writing.PartWriteInfo import KPartWriteInfo
from interchange.Enums.EnumDocument import Capability

# the measured single part relation extends the format capability without changing assembly admission
KNativeWriteCaps = KAsmWriteCaps | {Capability.KExpressions}

# the canonical format dispatches admitted part assembly and blank drawing destinations through one native writer
KSldWriteInfo = ReplaceValue(
    KPartWriteInfo,
    extensions=(*KPartWriteInfo.extensions, KAsmSuffix, KDrawingSuffix),
    aliases=(KAsmFormatId, KDrawingFormatId),
    capabilities=KNativeWriteCaps,
    native_capabilities=KNativeWriteCaps,
    assembly_extensions=(KAsmSuffix,),
    media_types=(
        "application/x-solidworks-part",
        "application/x-solidworks-assembly",
        "application/x-solidworks-drawing",
    ),
)
