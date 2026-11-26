from interchange.Enums.EnumDocument import Capability

# the ordinary line loop builder preserves only its modeled sketch support feature dimension configuration and body domains
KPartWriteCaps = frozenset(
    {
        Capability.KParameters,
        Capability.KParamHistory,
        Capability.KSupportPlanes,
        Capability.KEditableSketches,
        Capability.KBodyStructure,
        Capability.KConfigurations,
    }
)
