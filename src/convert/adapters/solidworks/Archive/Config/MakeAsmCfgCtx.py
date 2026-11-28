from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyUsage import BodyUsage
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.Assemblies.AsmCfgFields import (
    KAsmCfgFields,
)
from convert.adapters.solidworks.Archive.Config.MakeConfigCtx import MakeConfigCtx
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode

# assembly model and occurrence descriptors have independently measured virtual targets
KAsmVirtuals = MappingProxyType(
    {
        ("moAssembly_c", 1000): None,
        ("moAssembly_c", 1016): False,
        ("moAssembly_c", 1208): "moAssembly_c.SerializeLWData",
        ("moAssembly_c", 1216): "moAssembly_c.SerializeResolvedData",
        ("moReference_c", 1000): "moFeature_c.SerializeXmlData",
        ("moReference_c", 1016): True,
        ("moReference_c", 1208): "moConcept_c.SerializeLWData",
        ("moReference_c", 1216): "moConcept_c.SerializeResolvedData",
        ("moExplViewManager_c", 1000): "moFeature_c.SerializeXmlData",
        ("moExplViewManager_c", 1016): True,
        ("moExplViewManager_c", 1208): "moConcept_c.SerializeLWData",
        ("moExplViewManager_c", 1216): "moConcept_c.SerializeResolvedData",
    }
)


# an owned assembly selects its distinct configuration vocabulary over the existing shared fields
def MakeAsmCfgCtx(
    VersionValue: int, HeaderValue: ArchiveNode, UsageValue: BodyUsage | None
) -> BodyContext:
    ContextValue = MakeConfigCtx(VersionValue, HeaderValue, UsageValue)
    ContextValue.LayoutsValue = dict(ContextValue.LayoutsValue) | KAsmCfgFields
    ContextValue.VirtualValue = dict(ContextValue.VirtualValue) | KAsmVirtuals
    ContextValue.SchemasValue = dict(ContextValue.SchemasValue) | {
        "moAssembly_c": (1,),
        "moCStringHandle_c": (1,),
        "moExplViewManager_c": (1,),
        "moExtFeature_c": (1,),
        "moExtObjectList_c": (1,),
        "moExtObject_c": (1,),
        "moFolder_c": (1,),
        "moReference_c": (1,),
    }
    return ContextValue
