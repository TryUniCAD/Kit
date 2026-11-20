from types import MappingProxyType

from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass

# the current relation manager owns a schema one serialized body
KRelMgrClass = RuntimeClass("moRelMgr_c", 1)

# the native feature color table has a schema zero descriptor
KFeatColorClass = RuntimeClass("moFeatColorTab_c", 0)

# the member reader admits only the measured concrete descriptors
KCfgMemberSchemas = MappingProxyType(
    {
        ClassValue.NameValue: (ClassValue.SchemaValue,)
        for ClassValue in (KRelMgrClass, KFeatColorClass)
    }
)
