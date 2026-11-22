from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.registry.RegistryErrors import RegistryError
from convert.adapters.base.SourceEvidenceKey import KSourceEvidence
from convert.adapters.solidworks.Core.Writing.AttachedBox.FindBoxProof import (
    FindBoxProof,
)
from interchange.Enums.EnumDocument import Capability
from interchange.document.Models.DocumentModel import CadDocument


# each published source evidence record must still match the concrete original and actual adapter
def BoxTransferCaps(
    Document: CadDocument, WriterValue: object, ResultValue: WriteResult
) -> frozenset[Capability] | None:
    ProofValue = FindBoxProof(WriterValue, Document)
    if ProofValue is None:
        return None
    if (
        ResultValue.MetadataMap.get(KSourceEvidence) != ProofValue.EvidenceValue
        or not ResultValue.IsVendorLoadable
        or not ResultValue.IsAppUsable
    ):
        raise RegistryError(
            "attached box result did not account for its verified source"
        )
    return ProofValue.NativeCaps
