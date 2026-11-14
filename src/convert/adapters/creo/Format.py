from __future__ import annotations

from types import MappingProxyType

from convert.adapters.base.AdapterInfo import AdapterInfo
from interchange.enums.EnumDocument import Capability

KFormatId = "creo.prt"

KSuffixes = (".prt",)

KAliases = ("prt", "creo", "proe")

KSectionNames = (
    "AllFeatur",
    "BasicData",
    "BasicText",
    "BasBasData",
    "BasFullData",
    "DEPDB_DATA",
    "FeatDefs",
    "FeatDefsDtm",
    "FeatDefsIndex",
    "FullMData",
    "GeomDepen",
    "Geomlists",
    "MdlRefInfo",
    "MdlStatus",
    "NovisGeom",
    "SolidPersistTable",
    "SolidPrimdata",
    "THMB_IMG_MAIN",
    "UnitSystemDef",
    "VisibGeom",
)

KInfoValue = AdapterInfo(
    format_id=KFormatId,
    name="PTC Creo Parametric",
    version="PSB",
    aliases=KAliases,
    extensions=KSuffixes,
    capabilities=frozenset(
        {
            Capability.KConfigurations,
            Capability.KNativePayloads,
            Capability.KProvenance,
            Capability.KRoundtripMeta,
        }
    ),
    native_capabilities=frozenset({Capability.KRoundtripMeta}),
    media_types=("application/x-ptc-creo-part",),
    part_extensions=KSuffixes,
)

KFormatInfo = MappingProxyType({"info": KInfoValue, "format_id": KFormatId})
