from __future__ import annotations

from interchange.document.models.DocumentModel import CadDocument

from convert.adapters.base.AdapterInfo import AdapterInfo
from convert.adapters.base.ContractTypes import KSourceType
from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.ProbeResult import ProbeResult
from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.creo.CreoFormat import CreoFormat
from convert.adapters.creo.Format import KFormatId
from convert.adapters.creo.Format import KInfoValue
from convert.adapters.creo.Header import ReadHeader
from convert.adapters.creo.Reader import ReadDocument
from convert.adapters.creo.Reader import SourceBytes
from convert.adapters.creo.Toc import ReadToc
from convert.adapters.creo.Writer import IsCreoPath
from convert.adapters.creo.Writer import WriteDocument


class CreoMetadata:

    @property
    def info(self) -> AdapterInfo:
        return KInfoValue

    def Probe(self, Source: KSourceType) -> ProbeResult:
        try:
            DataValue, _ = SourceBytes(Source)
            HeaderValue = ReadHeader(DataValue)
            TocValue = ReadToc(DataValue, HeaderValue.base)
        except (CreoFormat, OSError, TypeError, ValueError) as ErrorInfo:
            return ProbeResult(KFormatId, 0.0, str(ErrorInfo))
        if TocValue.entries:
            return ProbeResult(
                KFormatId,
                1.0,
                f"{HeaderValue.kind} PSB with {len(TocValue.entries)} sections",
            )
        return ProbeResult(KFormatId, 0.7, "PSB header without valid sections")

    probe = Probe


class CreoReader:

    def Read(
        self, Source: KSourceType, Options: ReadOptions | None = None
    ) -> CadDocument:
        return ReadDocument(Source, Options)

    read = Read


class CreoSupport:

    def Supports(self, DocumentValue: CadDocument, Target: KTargetType) -> bool:
        return IsCreoPath(Target) and isinstance(
            DocumentValue.metadata.get("creo.source_bytes"), bytes
        )

    supports = Supports


class CreoWriter:

    def Write(
        self,
        DocumentValue: CadDocument,
        Target: KTargetType,
        Options: WriteOptions | None = None,
    ) -> WriteResult:
        return WriteDocument(DocumentValue, Target, Options)

    write = Write


class CreoAdapter(CreoMetadata, CreoReader, CreoSupport, CreoWriter):
    __slots__ = ()
