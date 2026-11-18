from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Container.Format import KAsmFormatId, KAsmSuffix
from convert.adapters.solidworks.Core.AssemblyPreparation.AsmWriteCaps import (
    KAsmWriteCaps,
)
from convert.adapters.solidworks.Core.Writing.PartWriteInfo import KPartWriteInfo

# the existing canonical reader alias domain requires one writer with separate qualified part and owned assembly destination subsets
KSldWriteInfo = ReplaceValue(
    KPartWriteInfo,
    extensions=(*KPartWriteInfo.extensions, KAsmSuffix),
    aliases=(KAsmFormatId,),
    capabilities=KAsmWriteCaps,
    native_capabilities=KAsmWriteCaps,
    assembly_extensions=(KAsmSuffix,),
    media_types=("application/x-solidworks-part", "application/x-solidworks-assembly"),
)
