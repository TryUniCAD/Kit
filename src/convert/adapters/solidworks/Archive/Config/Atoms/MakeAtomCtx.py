from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.AtomFields import (
    KAtomFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.ConceptFields import (
    KConceptFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.FeatureFields import (
    KFeatureFields,
)
from convert.adapters.solidworks.Archive.Config.Atoms.AtomTypes import (
    KAtomSchemas,
    KAtomVirtuals,
)

# the bounded atom uses the existing lightweight and resolved concept field owners
KAtomLayouts = MappingProxyType({**KFeatureFields, **KConceptFields, **KAtomFields})


# archive version guards must precede embedded manager and atom traversal
def MakeAtomCtx(VersionValue: int) -> BodyContext:
    if type(VersionValue) is not int or VersionValue != 19000:
        raise BodyUnsupported("SOLIDWORKS atom manager requires archive version 19000")
    return BodyContext(VersionValue, KAtomLayouts, KAtomVirtuals, KAtomSchemas)
