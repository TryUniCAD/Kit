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

# the observed thread map uses a concrete schema one descriptor when present
KThreadMgrClass = RuntimeClass("moCThreadRefMgr_c", 1)

# the kernel mark has its own schema and position in the same part map
KPMarkClass = RuntimeClass("moPMarkRecord_c", 1)

# standard part views use a distinct descriptor from annotation and exploded views
KViewClass = RuntimeClass("moView_c", 1)

# these bounded roles require concrete owners in the qualified profiles
KRequiredMembers = MappingProxyType(
    {KRelMgrClass: "relation", KPMarkClass: "partition mark", KViewClass: "view"}
)


# the member reader admits only the measured concrete descriptors
KCfgMemberSchemas = MappingProxyType(
    {
        ClassValue.NameValue: (ClassValue.SchemaValue,)
        for ClassValue in (
            KRelMgrClass,
            KFeatColorClass,
            KSketchBlockClass,
            KExplViewClass,
            KThreadMgrClass,
            KPMarkClass,
            KViewClass,
        )
    }
)
