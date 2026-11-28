from interchange import CadDocument, Capability
from interchange import infer_capabilities as InferCaps


# inferred document capabilities ensure writers account for semantics beyond declared flags
def GetDocumentCaps(DocumentData: CadDocument) -> frozenset[Capability]:
    RoundtripCap = next(
        CapabilityData
        for CapabilityData in Capability
        if CapabilityData.value == "roundtrip_metadata"
    )
    InferredCaps = InferCaps(
        DocumentData,
        roundtrip_metadata=(RoundtripCap in DocumentData.capabilities),
    )
    return DocumentData.capabilities | InferredCaps
