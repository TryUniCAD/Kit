from pathlib import Path as FilePath

from convert.adapters.base.AdapterInfo import AdapterInfo
from convert.adapters.base.ContractTypes import IsBinaryTarget, KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteOptions import PairProtocol
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.solidworks.Container.Format import KPartSuffix
from convert.adapters.solidworks.Core.AssemblyWriting.Nested.CanWriteNested import (
    CanWriteNested,
)
from convert.adapters.solidworks.Core.AssemblyWriting.Nested.EmitNestedMut import (
    EmitNestedMut,
)
from convert.adapters.solidworks.Core.Preparation.PlanPartWrite import PlanPartWrite
from convert.adapters.solidworks.Core.Preparation.Readback.ColdReadInput import (
    ColdReadInput,
)
from convert.adapters.solidworks.Core.Preparation.Readback.IsColdRead import IsColdRead
from convert.adapters.solidworks.Core.Writing.EmitNativeMut import EmitNativeMut
from convert.adapters.solidworks.Core.Writing.SldWriteInfo import KSldWriteInfo
from interchange.document.Models.DocumentModel import CadDocument


# one canonical writer retains the standalone part route and adds owned rigid assembly bundles
class SldprtWriter(PairProtocol):
    __slots__ = ()

    # shared discovery identifies both destinations with their own measured publication gates
    @property
    def info(self) -> AdapterInfo:
        return KSldWriteInfo

    # measured part evidence belongs to a complete standalone caller stream
    @property
    def IsWholeStream(self) -> bool:
        return True

    # the projection must reject unsupported neutral data in selection before the registry creates a staging target
    def supports(self, DocValue: CadDocument, Target: KTargetType) -> bool:
        if DocValue.assembly is not None:
            return CanWriteNested(DocValue, Target)
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
        if document.assembly is not None:
            return EmitNestedMut(document, destination, options)
        return EmitNativeMut(document, destination, options)
