from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyUsage import BodyUsage
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.Part.PartLayouts import (
    KPartLayouts,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.Part.PartSchemas import (
    KPartSchemas,
)
from convert.adapters.solidworks.Archive.Bodies.NewBodyUsage import NewBodyUsage
from convert.adapters.solidworks.Archive.Cmgr.ManagerFields import KManagerRecordRules
from convert.adapters.solidworks.Archive.Cmgr.UseLinkedCtxMut import UseLinkedCtxMut

# manager and part configuration records use distinct section and feature dispatch
KManagerVirtuals = MappingProxyType(
    {
        ("moConfigurationMgr_c", 0x4B8): "moConcept_c.SerializeLWData",
        ("moConfigurationMgr_c", 0x4C0): None,
        ("moConfigurationMgr_c", 0x3F8): False,
        ("moConfigurationMgr_c", 0x3E8): None,
        ("moPartConfiguration_c", 0x4B8): "moConcept_c.SerializeLWData",
        ("moPartConfiguration_c", 0x4C0): None,
        ("moPartConfiguration_c", 0x3F8): True,
        ("moPartConfiguration_c", 0x3E8): "moFeature_c.SerializeXmlData",
    }
)


# manager admission retains its distinct registry while sharing ordinary version and evidence guards
def MakeCmgrContext(
    VersionValue: int, UsageValue: BodyUsage | None, *, ReadLinked: bool = False
) -> BodyContext:
    ContextValue = BodyContext(
        VersionValue,
        KPartLayouts | KManagerRecordRules,
        KManagerVirtuals,
        KPartSchemas
        | {
            "moConfigurationMgr_c": (1,),
            "moCustomPropertyList": (1,),
            "moPartConfiguration_c": (1,),
        },
        NewBodyUsage(VersionValue, UsageValue),
    )
    if ReadLinked:
        UseLinkedCtxMut(ContextValue)
    return ContextValue
