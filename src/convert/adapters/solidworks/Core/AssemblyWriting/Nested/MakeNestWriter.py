from convert.adapters.base.AdapterInfo import AdapterInfo
from convert.adapters.base.AdapterProtocols import CadWriterAdapter
from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import PairProtocol, WriteOptions
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.solidworks.Core.AssemblyWriting.Nested.CanWriteNested import (
    CanWriteNested,
)
from convert.adapters.solidworks.Core.AssemblyWriting.Nested.EmitDraftMut import (
    EmitDraftMut,
)
from convert.adapters.solidworks.Core.Writing.SldWriteInfo import KSldWriteInfo
from interchange.document.Models.DocumentModel import CadDocument


# a factory local adapter keeps internal publication out of package discovery
def MakeNestWriter(WrittenAt: int) -> CadWriterAdapter:

    # the registry may stage only the independently admitted nested profile
    class NestWriter(PairProtocol):

        # the private registry uses the existing native format and transfer contract
        @property
        def info(self) -> AdapterInfo:
            return KSldWriteInfo

        # the registry performs ordinary document and path selection before staging
        def supports(self, DocValue: CadDocument, Target: KTargetType) -> bool:
            return CanWriteNested(DocValue, Target)

        # all generated members share the selected save event and the staged registry target
        def write(
            self,
            document: CadDocument,
            destination: KTargetType,
            options: WriteOptions | None = None,
        ) -> WriteResult:
            return EmitDraftMut(document, destination, options, WrittenAt)

    return NestWriter()
