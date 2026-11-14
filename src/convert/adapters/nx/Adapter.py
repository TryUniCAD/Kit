from __future__ import annotations as Annotations

from convert.adapters.base.AdapterInfo import AdapterInfo
from convert.adapters.base.ContractTypes import KSourceType, KTargetType
from convert.adapters.base.ProbeResult import ProbeResult
from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.nx.Format import KInfoValue
from convert.adapters.nx.Reader import ProbeNx, ReadNx
from convert.adapters.nx.Writer import CanSupportNx, WriteNx
from interchange.document.models.DocumentModel import CadDocument


# the nx adapter exposes one native reader and one native container writer
class NxAdapter:

    # registry discovery needs metadata before any source is opened
    @property
    def Info(self) -> AdapterInfo:
        return KInfoValue

    info = Info

    # probing ranks native nx containers without decoding geometry
    def Probe(self, Source: KSourceType) -> ProbeResult:
        return ProbeNx(Source)

    # lowercase probing keeps the public adapter protocol stable
    def probe(self, source: KSourceType) -> ProbeResult:
        return self.Probe(source)

    # reading projects native geometry and retains the exact source container
    def Read(
        self, Source: KSourceType, Options: ReadOptions | None = None
    ) -> CadDocument:
        return ReadNx(Source, Options)

    # lowercase reading keeps the public adapter protocol stable
    def read(
        self, source: KSourceType, options: ReadOptions | None = None
    ) -> CadDocument:
        return self.Read(source, options)

    # writing accepts only documents that retain an nx native container
    def Supports(self, DocValue: CadDocument, Target: KTargetType) -> bool:
        return CanSupportNx(DocValue, Target)

    # lowercase support keeps the public adapter protocol stable
    def supports(self, document: CadDocument, destination: KTargetType) -> bool:
        return self.Supports(document, destination)

    # writing rebuilds the native container from parsed streams
    def Write(
        self,
        DocValue: CadDocument,
        Target: KTargetType,
        Options: WriteOptions | None = None,
    ) -> WriteResult:
        return WriteNx(DocValue, Target, Options)

    # lowercase writing keeps the public adapter protocol stable
    def write(
        self,
        document: CadDocument,
        destination: KTargetType,
        options: WriteOptions | None = None,
    ) -> WriteResult:
        return self.Write(document, destination, options)


# the public adapter alias keeps the established class name
NxAdapterError = ValueError

# the public annotations binding keeps the established adapter metadata name
annotations = Annotations
