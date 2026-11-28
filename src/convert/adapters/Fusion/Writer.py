from convert.adapters.base.AdapterInfo import AdapterInfo
from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.Fusion.Bridge.WriterInfo import KWriterInfo
from interchange.document.Models.DocumentModel import CadDocument
from convert.adapters.Fusion.Bridge.EmitFuseMut import EmitFuseMut


# the fusion writer contract needs a dedicated boundary so public document claims remain grounded in native records
class FusionWriter:

    # the typed materials contract needs a shared interpretation so public document claims remain grounded in native records
    @property
    def TypedMaterials(self) -> bool:
        return True

    # an f3d archive must occupy the whole caller stream for its measured digest to apply
    @property
    def IsWholeStream(self) -> bool:
        return True

    # the info contract needs a shared interpretation so public document claims remain grounded in native records
    @property
    def Info(self) -> AdapterInfo:
        return KWriterInfo

    info = Info

    # the supports contract needs a shared interpretation so public document claims remain grounded in native records
    def Supports(self, Document: CadDocument, Target: KTargetType) -> bool:
        return set(Document.metadata) in ({"fusion.authoring"}, {"fusion.native_state"})

    # the supports contract needs a shared interpretation so public document claims remain grounded in native records
    def supports(self, document: CadDocument, destination: KTargetType) -> bool:
        return self.Supports(document, destination)

    # the write contract needs a consistent construction rule so public document claims remain grounded in native records
    def Write(
        self,
        Document: CadDocument,
        Target: KTargetType,
        Options: WriteOptions | None = None,
    ) -> WriteResult:
        return EmitFuseMut(Document, Target, Options)

    # the write contract needs a shared interpretation so public document claims remain grounded in native records
    def write(
        self,
        document: CadDocument,
        destination: KTargetType,
        options: WriteOptions | None = None,
    ) -> WriteResult:
        return self.Write(document, destination, options)
