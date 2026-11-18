from convert.adapters.solidworks.Core.Preparation.PartCaps import KPartWriteCaps
from interchange.Enums.EnumDocument import Capability

# capability admission must remain limited to the complete owned part and measured ordinary planar assembly domains
KAsmWriteCaps = KPartWriteCaps | frozenset(
    {Capability.KAssemblies, Capability.KAssemblyMates, Capability.KComponentDocs}
)
