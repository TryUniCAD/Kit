from pathlib import Path as FilePath

from convert.adapters.base.AdapterInfo import AdapterInfo
from convert.adapters.base.ContractTypes import IsBinaryTarget, KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteOptions import PairProtocol
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.solidworks.Container.Format import KPartSuffix
from convert.adapters.solidworks.Core.Preparation.Ellipse.IsColdEllip import IsColdEllip
from convert.adapters.solidworks.Core.Preparation.Ellipse.ReadColdEllip import (
    ReadColdEllip,
)
from convert.adapters.solidworks.Core.Preparation.Ellipse.IsEllipsePart import (
    IsEllipsePart,
)
from convert.adapters.solidworks.Core.Preparation.Ellipse.PlanEllipse import PlanEllipse
from convert.adapters.solidworks.Core.Preparation.PlanPartWrite import PlanPartWrite
from convert.adapters.solidworks.Core.Preparation.Readback.ColdReadInput import (
    ColdReadInput,
)
from convert.adapters.solidworks.Core.Preparation.Readback.IsColdRead import IsColdRead
from convert.adapters.solidworks.Core.Writing.Ellipse.EmitEllipMut import EmitEllipMut
from convert.adapters.solidworks.Core.Writing.EmitNativeMut import EmitNativeMut
from convert.adapters.solidworks.Core.Writing.PartWriteInfo import KPartWriteInfo
from interchange.document.Models.DocumentModel import CadDocument


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
        PathValue = FilePath(Target) if isinstance(Target, (str, FilePath)) else None
        try:
            if IsColdEllip(DocValue):
                _, PlanValue = ReadColdEllip(DocValue)
                NameValue = PlanValue.NameValue
            else:
                NameValue = ReadPartName(DocValue, PathValue)
        except (IndexError, TypeError, ValueError):
            return False
        if PathValue is not None:
            return (
                PathValue.suffix.casefold() == KPartSuffix
                and PathValue.stem == NameValue
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
        if IsEllipsePart(document):
            return EmitEllipMut(document, destination, options)
        return EmitNativeMut(document, destination, options)


# both ordinary and authored conic selection reuse their normal model qualification
def ReadPartName(DocumentValue: CadDocument, PathValue: FilePath | None) -> str:
    if IsColdRead(DocumentValue):
        NameValue = (
            PathValue.stem if PathValue is not None else DocumentValue.sketches[0].name
        )
        return PlanPartWrite(ColdReadInput(DocumentValue, NameValue)).NameValue
    return (
        PlanEllipse(DocumentValue).NameValue
        if IsEllipsePart(DocumentValue)
        else PlanPartWrite(DocumentValue).NameValue
    )
