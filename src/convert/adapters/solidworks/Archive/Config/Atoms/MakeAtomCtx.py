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


# atom state and stamp reads depend on these two native archive condition bits
KAtomConditions = 0x400080


# validated archive conditions must reach both the embedded manager and its atoms
def MakeAtomCtx(VersionValue: int, ConditionBits: int) -> BodyContext:
    if type(VersionValue) is not int or VersionValue != 19000:
        raise BodyUnsupported("SOLIDWORKS atom manager requires archive version 19000")
    if type(ConditionBits) is not int or ConditionBits & ~KAtomConditions:
        raise BodyUnsupported("unsupported SOLIDWORKS atom manager context")
    return BodyContext(
        VersionValue,
        KAtomLayouts,
        KAtomVirtuals,
        KAtomSchemas,
        FlagsValue={"conditions": ConditionBits},
    )
