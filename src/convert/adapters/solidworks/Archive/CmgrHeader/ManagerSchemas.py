from types import MappingProxyType

from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass

# the current directory has a concrete manager root descriptor
KManagerClass = RuntimeClass("dmConfigMgrHeader_c", 1)

# embedded list entries refer to one concrete configuration header descriptor
KConfigHdrClass = RuntimeClass("dmConfigHeader_c", 1)

# descriptor admission uses the two current native class schemas
KManagerSchemas = MappingProxyType(
    {
        KManagerClass.NameValue: (KManagerClass.SchemaValue,),
        KConfigHdrClass.NameValue: (KConfigHdrClass.SchemaValue,),
    }
)
