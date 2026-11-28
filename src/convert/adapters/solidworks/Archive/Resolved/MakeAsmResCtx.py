from collections.abc import Mapping
from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.BodyUsage import BodyUsage
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.Assemblies.AsmCfgFields import (
    KAsmCfgFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.AssemblyFields import (
    KAssemblyFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.ResolvedLayouts import (
    KResolvedLayouts,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.ResolvedSchemas import (
    KResolvedSchemas,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.ResolvedVirtuals import (
    KResolvedVirtuals,
)
from convert.adapters.solidworks.Archive.Bodies.NewBodyUsage import NewBodyUsage
from convert.adapters.solidworks.Archive.Config.MakeAsmCfgCtx import KAsmVirtuals
from convert.adapters.solidworks.Archive.Maps.MapSnapshot import MapSnapshot
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Resolved.FindModelRoot import FindModelRoot

# assembly folders and component features select the native virtual slots for this stream
KAsmResVirtuals = MappingProxyType(
    {
        ("moLiveSectionFolder_c", 1000): "moFeature_c.SerializeXmlData",
        ("moMateGroup_c", 1000): "moFeature_c.SerializeXmlData",
        ("moLiveSectionFolder_c", 1016): True,
        ("moMateGroup_c", 1016): True,
        ("moCompFeature_c", 1208): None,
        ("moCompFeature_c", 1216): None,
        ("moLiveSectionFolder_c", 1208): "moConcept_c.SerializeLWData",
        ("moLiveSectionFolder_c", 1216): "moConcept_c.SerializeResolvedData",
        ("moMateGroup_c", 1208): "moConcept_c.SerializeLWData",
        ("moMateGroup_c", 1216): "moConcept_c.SerializeResolvedData",
    }
)


# rigid assemblies resume the actual configuration allocations and their independent resolved vocabulary
def MakeAsmResCtx(
    VersionValue: int,
    SeedValue: MapSnapshot,
    LinkContext: Mapping[str, int],
    UsageValue: BodyUsage | None,
) -> BodyContext:
    OwnerValue = FindModelRoot(SeedValue)
    if (
        OwnerValue.ClassValue != RuntimeClass("moAssembly_c", 1)
        or dict(LinkContext)
        != {
            "model_compressed_stream": 1,
            "model_is_part": 0,
            "cmgr_f658": 0,
        }
        or any(type(Value) is not int for Value in LinkContext.values())
    ):
        raise BodyUnsupported(
            "SOLIDWORKS resolved graph needs its actual rigid assembly owner"
        )
    return BodyContext(
        VersionValue,
        dict(KResolvedLayouts) | KAsmCfgFields | KAssemblyFields,
        dict(KResolvedVirtuals) | KAsmVirtuals | KAsmResVirtuals,
        dict(KResolvedSchemas)
        | {
            "moAtomFeature_c": (1,),
            "moCompFeature_c": (1,),
            "moLiveSectionFolder_c": (1,),
            "moMateGroup_c": (1,),
        },
        NewBodyUsage(VersionValue, UsageValue),
        FlagsValue=dict(LinkContext),
        PartRootValue=OwnerValue,
    )
