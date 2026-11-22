from time import time as ReadTime

from convert.adapters.base.AdapterInfo import AdapterInfo
from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteOptions import PairProtocol
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.registry.EquationWrite import CheckEquations
from convert.adapters.registry.InchWrite import CheckInchWrite
from convert.adapters.registry.NativeWrite import CheckNative
from convert.adapters.registry.NativeReadOnly import CheckReadOnly
from convert.adapters.registry.ResearchWrite import CheckResearch
from convert.adapters.registry.SupportWrite import CheckSupports
from convert.adapters.solidworks.Core.AssemblyWriting.EmitAsmMut import EmitAsmMut
from convert.adapters.solidworks.Core.AssemblyWriting.Nested.CanWriteNested import (
    CanWriteNested,
)
from convert.adapters.solidworks.Core.AssemblyWriting.Nested.EmitNestedMut import (
    EmitNestedMut,
)
from convert.adapters.solidworks.Core.AssemblyWriting.QualifyAsm import QualifyNested
from convert.adapters.solidworks.Core.DrawingWriting.EmitBlankDrawingMut import (
    EmitBlankMut,
)
from convert.adapters.solidworks.Core.Writing.AttachedBox.EmitBoxMut import EmitBoxMut
from convert.adapters.solidworks.Core.Writing.AttachedBox.IsBoxSource import IsBoxSource
from convert.adapters.solidworks.Core.Writing.EmitNativeMut import EmitNativeMut
from convert.adapters.solidworks.Core.Writing.SldWriteInfo import KSldWriteInfo
from convert.adapters.solidworks.Core.Writing.CanWriteSldDoc import CanWriteSldDoc
from convert.adapters.solidworks.Core.Writing.StockEndWriter import StockEndWriter
from convert.adapters.solidworks.Core.Preparation.Readback.IsColdRead import IsColdRead
from convert.adapters.solidworks.Core.Preparation.Revolve.Readback.IsRevRead import IsRevRead
from convert.adapters.base.Materials.CheckMatState import CheckMatState
from convert.Formats.CheckSourceText import CheckSourceText
from interchange.document.Models.DocumentModel import CadDocument


# the canonical writer admits the modeled part owned assembly and authored blank drawing profiles
class SldprtWriter(StockEndWriter, PairProtocol):
    __slots__ = ()

    KTypedDrawings = True

    # the registry needs independent write metadata to retain the existing assembly and drawing reader aliases
    @property
    def info(self) -> AdapterInfo:
        return KSldWriteInfo

    # measured part families require the registry to check the actual standalone destination
    def IsWholeStream(self, DocumentValue: CadDocument) -> bool:
        return DocumentValue.assembly is None and DocumentValue.DrawingValue is None

    # the projection must reject unsupported neutral data in selection before the registry creates a staging target
    def supports(self, DocValue: CadDocument, Target: KTargetType) -> bool:
        return CanWriteSldDoc(DocValue, Target)

    # the public structural writer protocol uses these keyword names across plugins and conversion
    def write(
        self,
        document: CadDocument,
        destination: KTargetType,
        options: WriteOptions | None = None,
    ) -> WriteResult:
        CheckMatState(document)
        CheckResearch(document)
        CheckInchWrite(document)
        CheckEquations(document)
        CheckSupports(document)
        CheckSourceText(document)
        if IsBoxSource(document):
            return EmitBoxMut(document, destination, options)
        if IsRevRead(document):
            CheckReadOnly(document)
        elif not IsColdRead(document):
            CheckNative(document, self, destination)
        if document.DrawingValue is not None:
            return EmitBlankMut(document, destination, options)
        if document.assembly is not None:
            if CanWriteNested(document, destination):
                return QualifyNested(
                    EmitNestedMut(document, destination, options, int(ReadTime()))
                )
            return EmitAsmMut(document, destination, options)
        return EmitNativeMut(document, destination, options)
