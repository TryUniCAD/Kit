from types import MappingProxyType

from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass

# the current relation manager owns a schema one serialized body
KRelMgrClass = RuntimeClass("moRelMgr_c", 1)

# the native feature color table has a schema zero descriptor
KFeatColorClass = RuntimeClass("moFeatColorTab_c", 0)

# the sketch block manager has a concrete schema and an embedded map backlink
KSketchBlockClass = RuntimeClass("moSketchBlockMgr_c", 1)

# the part exploded view manager owns a separate inherited feature body and map
KExplViewClass = RuntimeClass("moPrtExplViewManager_c", 1)

# the member reader admits only the measured concrete descriptors
KCfgMemberSchemas = MappingProxyType(
    {
        ClassValue.NameValue: (ClassValue.SchemaValue,)
        for ClassValue in (
            KRelMgrClass,
            KFeatColorClass,
            KSketchBlockClass,
            KExplViewClass,
        )
    }
)
