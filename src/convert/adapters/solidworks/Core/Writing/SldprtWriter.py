from pathlib import Path as FilePath

from convert.adapters.base.AdapterInfo import AdapterInfo
from convert.adapters.base.ContractTypes import IsBinaryTarget, KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteOptions import PairProtocol
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.registry.EquationWrite import CheckEquations
from convert.adapters.registry.InchWrite import CheckInchWrite
from convert.adapters.registry.NativeWrite import CheckNative
from convert.adapters.registry.ResearchWrite import CheckResearch
from convert.adapters.registry.SupportWrite import CheckSupports
from convert.adapters.solidworks.Container.Format import KPartSuffix
from convert.adapters.solidworks.Core.AssemblyWriting.CanWriteAsm import CanWriteAsm
from convert.adapters.solidworks.Core.AssemblyWriting.EmitAsmMut import EmitAsmMut
from convert.adapters.solidworks.Core.DrawingWriting.CanWriteBlankDrawing import (
    CanWriteBlank,
)
from convert.adapters.solidworks.Core.DrawingWriting.EmitBlankDrawingMut import (
    EmitBlankMut,
)
from convert.adapters.solidworks.Core.Preparation.Imports.PlanImportPart import (
    PlanImportPart,
)
from convert.adapters.solidworks.Core.Preparation.PlanNativePart import PlanNativePart
from convert.adapters.solidworks.Core.Writing.EmitNativeMut import EmitNativeMut
from convert.adapters.solidworks.Core.Writing.SldWriteInfo import KSldWriteInfo
from interchange.document.Models.DocumentModel import CadDocument


# the canonical writer admits the modeled part owned assembly and authored blank drawing profiles
class SldprtWriter(PairProtocol):
    __slots__ = ()

    KTypedDrawings = True

    # the registry needs independent write metadata to retain the existing assembly and drawing reader aliases
    @property
    def info(self) -> AdapterInfo:
        return KSldWriteInfo

    # the projection must reject unsupported neutral data in selection before the registry creates a staging target
    def supports(self, DocValue: CadDocument, Target: KTargetType) -> bool:
        if DocValue.DrawingValue is not None:
            return CanWriteBlank(DocValue, Target)
        if DocValue.assembly is not None:
            return CanWriteAsm(DocValue, Target)
        try:
            if DocValue.brep is not None:
                _ = PlanImportPart(DocValue, Target)
                return True
            PlanValue = PlanNativePart(DocValue)
        except (TypeError, ValueError):
            return False
        if isinstance(Target, (str, FilePath)):
            PathValue = FilePath(Target)
            return (
                PathValue.suffix.casefold() == KPartSuffix
                and PathValue.stem == PlanValue.NameValue
            )
        return IsBinaryTarget(Target)

    # the public structural writer protocol uses these keyword names across plugins and conversion
    def write(
        self,
        document: CadDocument,
        destination: KTargetType,
        options: WriteOptions | None = None,
    ) -> WriteResult:
        CheckResearch(document)
        CheckInchWrite(document)
        CheckEquations(document)
        CheckSupports(document)
        CheckNative(document)
        if document.DrawingValue is not None:
            return EmitBlankMut(document, destination, options)
        if document.assembly is not None:
            return EmitAsmMut(document, destination, options)
        return EmitNativeMut(document, destination, options)
