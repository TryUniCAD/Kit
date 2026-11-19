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

# the canonical format dispatches admitted part, assembly and blank drawing destinations through one native writer
KSldWriteInfo = ReplaceValue(
    KPartWriteInfo,
    extensions=(*KPartWriteInfo.extensions, KAsmSuffix, KDrawingSuffix),
    aliases=(KAsmFormatId, KDrawingFormatId),
    capabilities=KAsmWriteCaps,
    native_capabilities=KAsmWriteCaps,
    assembly_extensions=(KAsmSuffix,),
    media_types=(
        "application/x-solidworks-part",
        "application/x-solidworks-assembly",
        "application/x-solidworks-drawing",
    ),
)
