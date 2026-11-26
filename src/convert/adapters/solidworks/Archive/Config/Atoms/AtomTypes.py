from types import MappingProxyType

from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass

# the atom manager reads inline fields while its rows have their own concrete class
KAtomClass = RuntimeClass("moAtom_c", 1)

# scoped part atom records must bind to the owning part already present in the archive
KPartClass = RuntimeClass("moPart_c", 1)

# resolved model fields dispatch the embedded manager without a tagged graph owner
KAtomMgrSchema = "moAtomManager_c.FUN_4bcef8d0"

# the current bounded reader admits only the concrete native atom body
KAtomSchemas = MappingProxyType({KAtomClass.NameValue: (KAtomClass.SchemaValue,)})

# the atom reaches both actual concept methods through the native node base
KAtomVirtuals = MappingProxyType(
    {
        (KAtomClass.NameValue, 1208): "moConcept_c.SerializeLWData",
        (KAtomClass.NameValue, 1216): "moConcept_c.SerializeResolvedData",
    }
)
