from interchange.Enums.EnumDocument import Capability

# these exact original domains carry source verification and byte ancestry
KBoxEvidenceCaps = frozenset(
    {Capability.KNativePayloads, Capability.KProvenance, Capability.KRoundtripMeta}
)

# independent ordinary source semantics must all pass through the native writer
KBoxSemanticCaps = frozenset(
    {
        Capability.KBrep,
        Capability.KBodyStructure,
        Capability.KConfigurations,
        Capability.KParameters,
        Capability.KParamHistory,
        Capability.KSupportPlanes,
    }
)
