from pathlib import Path as FilePath

from convert.adapters.base.AdapterInfo import AdapterInfo
from convert.adapters.base.ContractTypes import IsBinaryTarget, KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteOptions import PairProtocol
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.solidworks.Container.Format import KPartSuffix
from convert.adapters.solidworks.Core.Preparation.PlanPartWrite import PlanPartWrite
from convert.adapters.solidworks.Core.Preparation.Readback.ColdReadInput import (
    ColdReadInput,
)
from convert.adapters.solidworks.Core.Preparation.Readback.IsColdRead import IsColdRead
from convert.adapters.solidworks.Core.Writing.EmitNativeMut import EmitNativeMut
from convert.adapters.solidworks.Core.Writing.PartWriteInfo import KPartWriteInfo
from interchange.document.Models.DocumentModel import CadDocument


from convert.adapters.solidworks.Core.Preparation.Imports.CanImportBox import CanImportBox
from convert.adapters.solidworks.Core.Preparation.Imports.HasBareBrep import HasBareBrep


# the bounded native writer reports only the standalone part formats and neutral feature combinations it can synthesize
class SldprtWriter(PairProtocol):
    __slots__ = ()

    # independent write metadata binds only the qualified part format while assembly lookup stays with the reader
    @property
    def info(self) -> AdapterInfo:
        return KPartWriteInfo

    # measured part evidence belongs to a complete standalone caller stream
    @property
    def IsWholeStream(self) -> bool:
        return True

    # the projection must reject unsupported neutral data in selection before the registry creates a staging target
    def supports(self, DocValue: CadDocument, Target: KTargetType) -> bool:
        if HasBareBrep(DocValue):
            return CanImportBox(DocValue, Target)
        PathValue = FilePath(Target) if isinstance(Target, (str, FilePath)) else None
        try:
            if IsColdRead(DocValue):
                NameValue = (
                    PathValue.stem
                    if PathValue is not None
                    else DocValue.sketches[0].name
                )
                DocValue = ColdReadInput(DocValue, NameValue)
            PlanValue = PlanPartWrite(DocValue)
        except (IndexError, TypeError, ValueError):
            return False
        if PathValue is not None:
            return (
                PathValue.suffix.casefold() == KPartSuffix
                and PathValue.stem == PlanValue.NameValue
                and not PathValue.is_dir()
            )
        return IsBinaryTarget(Target)

    # the public structural writer protocol uses these keyword names across plugins and conversion
    def write(
        self,
        document: CadDocument,
        destination: KTargetType,
        options: WriteOptions | None = None,
    ) -> WriteResult:
        return EmitNativeMut(document, destination, options)
