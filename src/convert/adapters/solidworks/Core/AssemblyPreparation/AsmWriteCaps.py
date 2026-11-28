from convert.adapters.solidworks.Core.Preparation.PartCaps import KPartWriteCaps
from interchange.Enums.EnumDocument import Capability

# rigid nested assemblies add their own component documents and occurrence hierarchy
KAsmWriteCaps = KPartWriteCaps | frozenset(
    {Capability.KAssemblies, Capability.KComponentDocs}
)
