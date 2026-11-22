from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyUsage import BodyUsage
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.Assemblies.AsmCfgFields import (
    KAsmCfgFields,
)
from convert.adapters.solidworks.Archive.Cmgr.Layouts.AsmMgrFields import (
    KAssemblyFields,
)
from convert.adapters.solidworks.Archive.Cmgr.Layouts.AsmMgrRefs import KAsmMgrRefs
from convert.adapters.solidworks.Archive.Cmgr.MakeCmgrContext import MakeCmgrContext


# assembly manager rows extend the shared manager grammar with actual selected configuration owners
def MakeAsmMgrCtx(VersionValue: int, UsageValue: BodyUsage | None) -> BodyContext:
    ContextValue = MakeCmgrContext(VersionValue, UsageValue)
    ContextValue.LayoutsValue = (
        dict(ContextValue.LayoutsValue) | KAsmCfgFields | KAssemblyFields | KAsmMgrRefs
    )
    ContextValue.SchemasValue = dict(ContextValue.SchemasValue) | {
        "moAssyMassPropsCache_c": (1,),
        "moCStringHandle_c": (1,),
        "moConfigObject_c": (1,),
        "moConfig_c": (1,),
        "moConfiguration_c": (1,),
        "moContextChainComponent_c": (1,),
        "moExtFeatureList_c": (1,),
        "moExtFeature_c": (1,),
        "moExtObject_c": (1,),
        "moReferenceChain_c": (1,),
    }
    ContextValue.VirtualValue = dict(ContextValue.VirtualValue) | {
        ("moConfiguration_c", 0x4B8): "moConcept_c.SerializeLWData",
        ("moConfiguration_c", 0x4C0): None,
        ("moConfiguration_c", 0x3F8): True,
        ("moConfiguration_c", 0x3E8): "moBaseConfiguration_c.SerializeXmlData",
    }
    return ContextValue
